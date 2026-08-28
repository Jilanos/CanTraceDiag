"""Reader for the Vector Binary Logging Format (``.blf``).

Unlike the ASC and TRC readers, which own their line grammar, this adapter
delegates container decoding to ``python-can``'s :class:`~can.io.blf.BLFReader`
and then re-normalizes every object into the project's own model. Nothing from
``python-can`` reaches the rest of the product: the adapter is the boundary.

Supported subset
----------------
Classic CAN data frames (BLF ``CAN_MESSAGE`` / ``CAN_MESSAGE2`` objects) with a
DLC of 0..8 and a payload whose length matches that DLC. Standard and extended
identifiers are both supported.

Everything else is retained as an inspectable :class:`NonDataEvent` rather than
being dropped or coerced into a malformed frame:

``ErrorFrame``
    A BLF ``CAN_ERROR_EXT`` object. Named to match the ASC reader so the trace
    view groups error frames across formats.
``BlfRemoteRequest``
    A remote-transmission-request frame. It carries no payload to decode, so it
    is surfaced as a diagnostic (the text TRC reader treats RTR the same way).
``BlfUnsupported``
    A CAN FD or CAN XL object. Out of scope for this product.
``BlfAnomaly``
    A classic-CAN object that failed an integrity check (DLC out of range,
    payload length disagreeing with the DLC, arbitration id out of range).

Container-level corruption is *not* a diagnostic. Once the object stream
desynchronizes, neither the remaining offsets nor the object ordering can be
trusted, so the adapter raises :class:`BlfImportError` and the caller discards
the whole import instead of publishing a partial trace.

Timestamps
----------
BLF stores object timestamps as an offset from a measurement start recorded in
the file header. ``python-can`` only exposes the two already summed, so the
adapter subtracts the header start back out to produce seconds since the start
of the acquisition -- the same origin the ASC and TRC readers use.

That round trip goes through a double, and when the header carries a real
wall-clock start (~1.8e9 s) its ulp is about 0.24 us, so the difference carries
sub-microsecond noise. Results are therefore quantized to microseconds, at or
below the resolution of the acquisition hardware this product targets, which
also makes the value deterministic across runs.

Channels
--------
``python-can`` reports a zero-based channel; BLF and Vector tooling number buses
from 1. The adapter restores the 1-based number and formats it as a string, so a
BLF channel reads like an ASC channel (``"1"``, ``"2"``, ...).
"""

from __future__ import annotations

import os
import struct
import zlib
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO

from can.io.blf import BLFParseError, BLFReader

from cantracediag.models import NonDataEvent, RawCanFrame

_CLASSIC_MAX_DLC = 8
_MAX_STANDARD_ID = 0x7FF
_MAX_EXTENDED_ID = 0x1FFFFFFF

# Timestamps are rounded to this many decimals; see the module docstring.
_TIMESTAMP_DECIMALS = 6

# Exceptions a corrupt or truncated container can surface from python-can's
# reader. They all mean the same thing to us: the object stream can no longer be
# trusted.
_CONTAINER_ERRORS = (BLFParseError, struct.error, zlib.error, EOFError, ValueError)


class BlfImportError(Exception):
    """The BLF container could not be read safely, so no trace is published."""


@dataclass(slots=True)
class BlfParseResult:
    frames: list[RawCanFrame]
    events: list[NonDataEvent]
    object_count: int
    parsed_frames: int
    parsed_events: int


class _Scanner:
    """Tracks how many BLF objects were normalized.

    Exposes ``base`` purely so a BLF import reports the same ``asc_base``
    field shape as a text import; a binary container has no numeric base.
    """

    def __init__(self) -> None:
        self.base = "hex"
        self.object_count = 0

    def feed(
        self, message: object, start_timestamp: float
    ) -> tuple[RawCanFrame | None, NonDataEvent | None]:
        self.object_count += 1
        return _normalize(message, start_timestamp)


def parse_blf(path: str | Path) -> BlfParseResult:
    """Read a BLF file eagerly into frames and diagnostic events."""
    frames: list[RawCanFrame] = []
    events: list[NonDataEvent] = []
    scanner, items = stream_blf(path)
    for item in items:
        if isinstance(item, RawCanFrame):
            frames.append(item)
        else:
            events.append(item)
    return BlfParseResult(frames, events, scanner.object_count, len(frames), len(events))


def stream_blf(
    path: str | Path,
    on_progress: Callable[[int], None] | None = None,
    progress_every: int = 5000,
) -> tuple[_Scanner, Iterator[RawCanFrame | NonDataEvent]]:
    """Stream normalized classic-CAN frames and diagnostic events.

    Objects are yielded in file order, so the caller's sequence numbering gives
    the same deterministic total order it gives an ASC or TRC import.

    ``on_progress``, when given, is called with the current byte offset in the
    file every ``progress_every`` objects and once more at end of file. The
    offset advances one compressed container at a time, which is what bounds
    peak memory: only one container is ever decompressed at once.
    """
    scanner = _Scanner()

    def _gen() -> Iterator[RawCanFrame | NonDataEvent]:
        with open(path, "rb") as handle:
            # BLFReader.stop() closes the handle once iteration ends, so the
            # closing progress call reports the file size rather than tell().
            total_bytes = os.fstat(handle.fileno()).st_size
            reader = _open_reader(handle)
            start = reader.start_timestamp or 0.0
            count = 0
            for message in _iter_messages(reader):
                count += 1
                frame, event = scanner.feed(message, start)
                if frame is not None:
                    yield frame
                if event is not None:
                    yield event
                if on_progress is not None and count % progress_every == 0:
                    on_progress(handle.tell())
            if on_progress is not None:
                on_progress(total_bytes)

    return scanner, _gen()


def _open_reader(handle: BinaryIO) -> BLFReader:
    """Open the container, mapping a bad header to a project-owned error."""
    try:
        return BLFReader(handle)
    except _CONTAINER_ERRORS as exc:
        raise BlfImportError(f"Not a readable BLF container: {exc}") from exc


def _iter_messages(reader: BLFReader) -> Iterator[object]:
    """Iterate objects, mapping mid-stream corruption to a project-owned error.

    The generator is advanced by hand so a failure raised from deep inside
    ``python-can`` is caught here rather than escaping as a library exception.
    """
    messages = iter(reader)
    while True:
        try:
            message = next(messages)
        except StopIteration:
            return
        except _CONTAINER_ERRORS as exc:
            raise BlfImportError(f"Corrupt BLF object stream: {exc}") from exc
        yield message


def _normalize(
    message: object, start_timestamp: float
) -> tuple[RawCanFrame | None, NonDataEvent | None]:
    timestamp = round(
        float(getattr(message, "timestamp", 0.0)) - start_timestamp,
        _TIMESTAMP_DECIMALS,
    )
    channel = _channel(getattr(message, "channel", None))

    if getattr(message, "is_error_frame", False):
        return None, NonDataEvent(timestamp, channel, "ErrorFrame", _describe(message))
    if getattr(message, "is_fd", False):
        return None, NonDataEvent(
            timestamp, channel, "BlfUnsupported", f"CAN FD/XL object: {_describe(message)}"
        )
    if getattr(message, "is_remote_frame", False):
        return None, NonDataEvent(
            timestamp, channel, "BlfRemoteRequest", _describe(message)
        )

    dlc = int(getattr(message, "dlc", 0) or 0)
    data = bytes(getattr(message, "data", b"") or b"")
    arbitration_id = int(getattr(message, "arbitration_id", 0) or 0)
    is_extended = bool(getattr(message, "is_extended_id", False))

    if not 0 <= dlc <= _CLASSIC_MAX_DLC:
        return None, NonDataEvent(
            timestamp, channel, "BlfAnomaly", f"classic CAN DLC {dlc} exceeds {_CLASSIC_MAX_DLC}"
        )
    if len(data) != dlc:
        return None, NonDataEvent(
            timestamp,
            channel,
            "BlfAnomaly",
            f"payload length {len(data)} does not match DLC {dlc}",
        )
    limit = _MAX_EXTENDED_ID if is_extended else _MAX_STANDARD_ID
    if not 0 <= arbitration_id <= limit:
        return None, NonDataEvent(
            timestamp,
            channel,
            "BlfAnomaly",
            f"arbitration id out of range {hex(arbitration_id)}",
        )

    return RawCanFrame(
        timestamp_s=timestamp,
        channel=channel,
        arbitration_id=arbitration_id,
        is_extended_id=is_extended,
        dlc=dlc,
        data=data,
        direction="Rx" if getattr(message, "is_rx", True) else "Tx",
        is_remote=False,
    ), None


def _channel(raw: object) -> str | None:
    """Map python-can's zero-based channel back to BLF's 1-based bus number."""
    if isinstance(raw, bool) or not isinstance(raw, int):
        return None
    number = raw + 1
    return str(number) if number >= 1 else None


def _describe(message: object) -> str:
    """Short, payload-free description used as a diagnostic detail."""
    arbitration_id = int(getattr(message, "arbitration_id", 0) or 0)
    dlc = int(getattr(message, "dlc", 0) or 0)
    kind = "extended" if getattr(message, "is_extended_id", False) else "standard"
    return f"id={hex(arbitration_id)} ({kind}) dlc={dlc}"
