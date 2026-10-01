"""Reader for raw CAN bus logging in ASAM MDF 4 (``.mf4``) measurements.

Like the BLF adapter, this module delegates container decoding to a library --
``asammdf`` -- and re-normalizes every record into the project's own model.
Nothing from ``asammdf`` reaches the rest of the product: the adapter is the
boundary, and ``asammdf`` is imported lazily so ASC/TRC/BLF imports never pay
for it.

Supported layout
----------------
MDF 4.x files (finalized ``MDF     `` or unfinalized ``UnFinMF ``) that follow
the ASAM MDF bus-logging convention: one channel group per logged frame type,
whose bus-event structure channel is named ``CAN_DataFrame`` with the child
channels ``.ID``, ``.DLC`` and ``.DataBytes``, and optionally ``.IDE``,
``.BusChannel``, ``.Dir``, ``.DataLength`` and ``.EDL``. Children may be stored
in the record or be MDF *virtual* channels whose constant value comes from a
conversion (third-party loggers use that for the bus number, direction and IDE
flag of a group), so every child is read as a physical value.

Normalization
-------------
* Timestamp: the group's master (time) channel in seconds, measurement relative.
  It is neither rebased per group nor converted to wall-clock time; it is
  rounded to nanoseconds to strip binary noise from the master conversion.
* Channel: the numeric ``BusChannel`` value as a string (``"1"``, ``"9"``), as
  recorded. Absent -> ``None`` (unknown, never invented).
* Direction: ``Dir`` 0 -> ``Rx``, 1 -> ``Tx`` (ASAM convention). Absent or any
  other value -> ``None``.
* Identifier: ``IDE`` decides standard/extended. Without ``IDE``, bit 31 of the
  ID (a common logger convention) or an ID above 0x7FF marks it extended.
* Payload: the first ``DataLength`` bytes of ``DataBytes`` (``DLC`` when there
  is no ``DataLength``). A classic frame must have DLC 0..8 and DataLength == DLC.

Everything else is surfaced, never dropped silently and never recoded as a
classic frame:

``ErrorFrame``           a ``CAN_ErrorFrame`` record (one event per record).
``Mf4RemoteRequest``     a ``CAN_RemoteFrame`` record (one event per record).
``Mf4Unsupported``       a CAN FD/XL data frame (``EDL`` set), one per record.
``Mf4Anomaly``           a classic frame failing an integrity check.
``Mf4Skipped``           one summary event per populated group that is not CAN
                         bus logging at all (LIN, FlexRay, signal-only data...).

Ordering
--------
Groups are merged chronologically (each group is expected in time order, as
loggers write it; a group whose time goes backwards is reported as a warning,
and the store's ``(timestamp_s, seq)`` order still places those records by
time). ``asammdf`` reads each group separately, so
the original interleaving of records that share a timestamp across groups is
not recoverable; ties are broken by ``(group index, record index)`` -- the order
of the channel groups in the file, then record order within a group. Equal
timestamps within one group keep their source order.

Unfinalized measurements
------------------------
A logger that stops without finalizing leaves stale metadata: zero cycle
counters and a last DT block whose length covers only its header. ``asammdf``
recovers that in a *temporary copy* it finalizes (the source file is opened
read-only and never modified); the copy lives in a directory this adapter
owns and removes. Because that recovery locates the end of the last DT block
by scanning for block signatures -- and silently drops a truncated trailing
record -- the adapter reconciles the result independently before yielding
anything: the bytes from the last DT header to end of file must be consumed
exactly by complete records. Any mismatch raises :class:`Mf4ImportError` and
no partial trace is published.
"""

from __future__ import annotations

import heapq
import math
import shutil
import struct
import tempfile
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from pathlib import Path

from cantracediag.models import NonDataEvent, RawCanFrame

_CLASSIC_MAX_DLC = 8
_MAX_STANDARD_ID = 0x7FF
_MAX_EXTENDED_ID = 0x1FFFFFFF
_EXTENDED_FLAG = 0x80000000

# Timestamps are rounded to nanoseconds; see the module docstring.
_TIMESTAMP_DECIMALS = 9

# Records read from one group per asammdf call. Bounds peak memory: at most one
# chunk per populated group is resident while the groups are merged.
_CHUNK_RECORDS = 20_000

_ID_BLOCK = struct.Struct("<8s8s8s4sH30sHH")
_BLOCK_HEADER = struct.Struct("<4s4sQQ")
_FLAG_LAST_DT_LENGTH = 0x4
_FLAG_LAST_DL = 0x10
_FLAG_CG_VLSD = 0x1

_FRAME_PREFIX = "CAN_DataFrame"
_REMOTE_PREFIX = "CAN_RemoteFrame"
_ERROR_PREFIX = "CAN_ErrorFrame"

_INSTALL_HINT = (
    "MF4 import needs the 'asammdf' package. Reinstall CanTraceDiag with its "
    "dependencies (pip install -e .) to enable it."
)


class Mf4ImportError(Exception):
    """The MF4 measurement could not be read safely, so no trace is published."""


@dataclass(slots=True)
class Mf4ParseResult:
    frames: list[RawCanFrame]
    events: list[NonDataEvent]
    record_count: int
    parsed_frames: int
    parsed_events: int


@dataclass(slots=True)
class _Scanner:
    """Import facts the caller can read once iteration completes.

    ``base`` only exists so an MF4 import reports the same ``asc_base`` field
    shape as a text import; a binary container has no numeric base.
    """

    base: str = "hex"
    version: str | None = None
    unfinalized_flags: int = 0
    record_count: int = 0
    warnings: list[str] = field(default_factory=list)

    @property
    def recovered(self) -> bool:
        return bool(self.unfinalized_flags)


@dataclass(slots=True)
class _Group:
    index: int
    name: str
    kind: str  # "frame" | "remote" | "error" | "skipped"
    cycles: int
    channels: dict[str, int]


def parse_mf4(path: str | Path) -> Mf4ParseResult:
    """Read an MF4 measurement eagerly into frames and diagnostic events."""
    frames: list[RawCanFrame] = []
    events: list[NonDataEvent] = []
    scanner, items = stream_mf4(path)
    for item in items:
        if isinstance(item, RawCanFrame):
            frames.append(item)
        else:
            events.append(item)
    return Mf4ParseResult(frames, events, scanner.record_count, len(frames), len(events))


def stream_mf4(
    path: str | Path,
    on_progress: Callable[[int], None] | None = None,
    cancel_check: Callable[[], bool] | None = None,
    chunk_records: int = _CHUNK_RECORDS,
) -> tuple[_Scanner, Iterator[RawCanFrame | NonDataEvent]]:
    """Stream normalized classic-CAN frames and diagnostic events in time order.

    ``on_progress`` receives a byte-offset estimate (records consumed scaled to
    the file size) so the pipeline's byte-based progress stays monotonic.
    ``cancel_check`` is polled while the container is opened and recovered and
    before every chunk read; when it returns ``True`` the import raises
    :class:`~cantracediag.pipeline.ImportCancelled`. Nothing is yielded before
    the container has passed the integrity reconciliation.
    """
    scanner = _Scanner()
    source = Path(path)

    def _gen() -> Iterator[RawCanFrame | NonDataEvent]:
        total_bytes = source.stat().st_size
        scanner.version, scanner.unfinalized_flags = _read_identification(source)
        _check_cancel(cancel_check)
        workdir = tempfile.mkdtemp(prefix="ctd_mf4_")
        mdf = None
        try:
            mdf = _open(source, workdir, cancel_check)
            _check_cancel(cancel_check)
            groups = _classify(mdf)
            _reconcile(mdf, source, scanner.unfinalized_flags, total_bytes)
            total_records = sum(g.cycles for g in groups if g.kind != "skipped")
            scanner.record_count = sum(g.cycles for g in groups)
            if scanner.recovered:
                scanner.warnings.append(
                    f"Recovered an unfinalized MDF {scanner.version} measurement "
                    f"(flags 0x{scanner.unfinalized_flags:02X}) from a temporary copy; "
                    "the source file was not modified."
                )

            streams = []
            backwards: dict[str, int] = {}
            for group in groups:
                if group.kind == "skipped":
                    event = _skipped_event(mdf, group)
                    scanner.warnings.append(event.detail or "")
                    streams.append(iter([((event.timestamp_s, group.index, 0), event)]))
                    continue
                streams.append(
                    _iter_group(mdf, group, chunk_records, cancel_check, backwards)
                )

            emitted = 0
            for _key, item in heapq.merge(*streams, key=lambda pair: pair[0]):
                yield item
                emitted += 1
                if on_progress is not None and emitted % 5000 == 0 and total_records:
                    on_progress(int(total_bytes * emitted / total_records))
            if on_progress is not None:
                on_progress(total_bytes)
            for name, count in backwards.items():
                scanner.warnings.append(
                    f"Time goes backwards {count} time(s) within group '{name}'; those "
                    "records are placed by timestamp, not by the group merge."
                )
        finally:
            if mdf is not None:
                mdf.close()
            shutil.rmtree(workdir, ignore_errors=True)

    return scanner, _gen()


# -- container -----------------------------------------------------------


def _read_identification(source: Path) -> tuple[str, int]:
    """Validate the 64-byte ID block read straight from the (untouched) source."""
    with open(source, "rb") as handle:
        raw = handle.read(_ID_BLOCK.size)
    if len(raw) < _ID_BLOCK.size:
        raise Mf4ImportError("Not an MDF file: identification block is truncated.")
    file_id, version_str, _prog, _res, _num, _res2, unfin_std, _unfin_custom = (
        _ID_BLOCK.unpack(raw)
    )
    if file_id not in (b"MDF     ", b"UnFinMF "):
        raise Mf4ImportError("Not an MDF file: unknown file identifier.")
    version = version_str.decode("ascii", "replace").strip(" \0")
    if not version.startswith("4."):
        raise Mf4ImportError(f"Unsupported MDF version {version}: only MDF 4.x is supported.")
    if file_id == b"UnFinMF " and not unfin_std:
        # An unfinalized identifier without flags gives no recovery contract.
        raise Mf4ImportError("Unfinalized MDF file without finalization flags.")
    return version, unfin_std if file_id == b"UnFinMF " else 0


def _open(source: Path, workdir: str, cancel_check: Callable[[], bool] | None):
    try:
        from asammdf import MDF
    except ImportError as exc:  # pragma: no cover - exercised only without the dep
        raise Mf4ImportError(_INSTALL_HINT) from exc

    def _progress(*_args) -> None:
        # asammdf reports once per channel group while it reads (and, for an
        # unfinalized file, recovers) the metadata: the only hook through which
        # a long initialization can be interrupted.
        _check_cancel(cancel_check)

    try:
        return MDF(source, temporary_folder=workdir, progress=_progress)
    except Exception as exc:
        if _is_cancel(exc):
            raise
        raise Mf4ImportError(f"Not a readable MF4 measurement: {type(exc).__name__}") from exc


def _classify(mdf) -> list[_Group]:
    groups: list[_Group] = []
    for index, group in enumerate(mdf.groups):
        cg = group.channel_group
        if cg.flags & _FLAG_CG_VLSD:
            continue  # VLSD storage groups carry data of another group
        cycles = int(cg.cycles_nr)
        if not cycles:
            continue  # declared but empty schema groups are not traffic
        names = {ch.name: i for i, ch in enumerate(group.channels)}
        kind = "skipped"
        if _FRAME_PREFIX in names:
            kind = "frame"
        elif _REMOTE_PREFIX in names:
            kind = "remote"
        elif _ERROR_PREFIX in names:
            kind = "error"
        if kind == "frame":
            missing = [f for f in (".ID", ".DLC", ".DataBytes") if _FRAME_PREFIX + f not in names]
            if missing:
                kind = "skipped"
        groups.append(_Group(index, cg.acq_name or f"group {index}", kind, cycles, names))
    return groups


def _reconcile(mdf, source: Path, unfinalized_flags: int, total_bytes: int) -> None:
    """Prove the recovered records account for every data byte of the source.

    Applies to data groups stored in a single DT block (the layout of
    third-party bus loggers). For an unfinalized file the last DT block is
    taken to extend to end of file -- the recovery hypothesis -- and is
    measured here from the untouched source rather than trusted from asammdf.
    """
    if unfinalized_flags & _FLAG_LAST_DL:
        raise Mf4ImportError(
            "Unfinalized data-list layout is not supported; the recording cannot be "
            "recovered safely."
        )
    by_dg: dict[int, list] = {}
    for group in mdf.groups:
        by_dg.setdefault(group.data_group.address, []).append(group)

    with open(source, "rb") as handle:
        layouts = []
        for dg_groups in by_dg.values():
            data_addr = dg_groups[0].data_group.data_block_addr
            if not data_addr:
                if any(g.channel_group.cycles_nr for g in dg_groups):
                    raise Mf4ImportError("Channel group has records but no data block.")
                continue
            handle.seek(data_addr)
            header = handle.read(_BLOCK_HEADER.size)
            if len(header) < _BLOCK_HEADER.size:
                raise Mf4ImportError("Data block lies beyond the end of the file.")
            block_id, _res, block_len, _links = _BLOCK_HEADER.unpack(header)
            layouts.append((data_addr, block_id, block_len, dg_groups))

    last_dt = max((a for a, bid, _l, _g in layouts if bid == b"##DT"), default=None)
    for data_addr, block_id, block_len, dg_groups in layouts:
        if block_id != b"##DT":
            if unfinalized_flags:
                raise Mf4ImportError(
                    "Unfinalized measurement with a non-DT data layout cannot be "
                    "verified; refusing a possibly partial import."
                )
            continue  # finalized lists/compressed blocks: lengths are authoritative
        if unfinalized_flags & _FLAG_LAST_DT_LENGTH and data_addr == last_dt:
            data_len = total_bytes - data_addr - _BLOCK_HEADER.size
        else:
            data_len = block_len - _BLOCK_HEADER.size
            if data_addr + block_len > total_bytes:
                raise Mf4ImportError("Data block is truncated: the file ends inside it.")
        rid_len = int(dg_groups[0].data_group.record_id_len)
        accounted = 0
        for group in dg_groups:
            cg = group.channel_group
            if cg.flags & _FLAG_CG_VLSD:
                if cg.cycles_nr and unfinalized_flags:
                    raise Mf4ImportError(
                        "Unfinalized measurement contains variable-length records whose "
                        "recovery cannot be verified."
                    )
                if cg.cycles_nr:
                    accounted = None
                    break
                continue
            record = rid_len + int(cg.samples_byte_nr) + int(cg.invalidation_bytes_nr)
            accounted += int(cg.cycles_nr) * record
        if accounted is None:
            continue  # finalized file with VLSD records: declared lengths stand
        if accounted != data_len:
            raise Mf4ImportError(
                f"Recovered records cover {accounted} of {data_len} data bytes; the "
                "recording is truncated or its layout is not understood."
            )


# -- records ---------------------------------------------------------------


def _iter_group(mdf, group: _Group, chunk_records: int, cancel_check, backwards: dict):
    prefix = {"frame": _FRAME_PREFIX, "remote": _REMOTE_PREFIX, "error": _ERROR_PREFIX}[
        group.kind
    ]
    fields = ("BusChannel", "ID", "IDE", "DLC", "DataLength", "DataBytes", "Dir", "EDL")
    wanted = {f: group.channels.get(f"{prefix}.{f}") for f in fields}
    wanted = {f: i for f, i in wanted.items() if i is not None}
    selection = [(None, group.index, i) for i in wanted.values()]

    previous = -math.inf
    for offset in range(0, group.cycles, chunk_records):
        _check_cancel(cancel_check)
        count = min(chunk_records, group.cycles - offset)
        try:
            signals = mdf.select(
                selection, record_offset=offset, record_count=count, copy_master=False
            ) if selection else []
            if selection:
                times = signals[0].timestamps
            else:
                times = mdf.get_master(group.index, record_offset=offset, record_count=count)
        except Exception as exc:
            if _is_cancel(exc):
                raise
            raise Mf4ImportError(
                f"Failed to read records of group {group.name}: {type(exc).__name__}"
            ) from exc
        if len(times) != count:
            raise Mf4ImportError(f"Group {group.name} returned an unexpected record count.")
        columns = {f: s.samples for f, s in zip(wanted, signals, strict=True)}
        for row in range(count):
            timestamp = float(times[row])
            if not math.isfinite(timestamp):
                raise Mf4ImportError(f"Non-finite timestamp in group {group.name}.")
            timestamp = round(timestamp, _TIMESTAMP_DECIMALS)
            if timestamp < previous:
                # The chronological merge assumes each group is in time order,
                # as loggers write it; say so when a group is not.
                backwards[group.name] = backwards.get(group.name, 0) + 1
            previous = timestamp
            values = {f: col[row] for f, col in columns.items()}
            item = _normalize(group.kind, timestamp, values)
            yield (timestamp, group.index, offset + row), item


def _normalize(kind: str, timestamp: float, values: dict) -> RawCanFrame | NonDataEvent:
    channel = _bus(values.get("BusChannel"))
    if kind == "error":
        return NonDataEvent(timestamp, channel, "ErrorFrame", "MF4 CAN_ErrorFrame record")

    raw_id = _int(values.get("ID"))
    dlc = _int(values.get("DLC"))
    ide = values.get("IDE")
    if raw_id is None:
        return NonDataEvent(timestamp, channel, "Mf4Anomaly", "missing or invalid ID")
    if ide is not None:
        is_extended = bool(_int(ide))
        arbitration_id = raw_id & ~_EXTENDED_FLAG if raw_id & _EXTENDED_FLAG else raw_id
    else:
        is_extended = bool(raw_id & _EXTENDED_FLAG) or raw_id > _MAX_STANDARD_ID
        arbitration_id = raw_id & ~_EXTENDED_FLAG
    describe = f"id={hex(arbitration_id)} ({'extended' if is_extended else 'standard'}) dlc={dlc}"

    if kind == "remote":
        return NonDataEvent(timestamp, channel, "Mf4RemoteRequest", describe)
    if _int(values.get("EDL")):
        return NonDataEvent(timestamp, channel, "Mf4Unsupported", f"CAN FD frame: {describe}")

    limit = _MAX_EXTENDED_ID if is_extended else _MAX_STANDARD_ID
    if not 0 <= arbitration_id <= limit:
        return NonDataEvent(
            timestamp, channel, "Mf4Anomaly", f"arbitration id out of range {hex(raw_id)}"
        )
    if dlc is None or not 0 <= dlc <= _CLASSIC_MAX_DLC:
        return NonDataEvent(
            timestamp, channel, "Mf4Anomaly", f"classic CAN DLC {dlc} exceeds {_CLASSIC_MAX_DLC}"
        )
    length = _int(values.get("DataLength")) if "DataLength" in values else dlc
    if length != dlc:
        return NonDataEvent(
            timestamp, channel, "Mf4Anomaly", f"data length {length} does not match DLC {dlc}"
        )
    payload = bytes(values.get("DataBytes", b""))
    if len(payload) < dlc:
        return NonDataEvent(
            timestamp, channel, "Mf4Anomaly", f"payload shorter than DLC ({len(payload)} < {dlc})"
        )

    return RawCanFrame(
        timestamp_s=timestamp,
        channel=channel,
        arbitration_id=arbitration_id,
        is_extended_id=is_extended,
        dlc=dlc,
        data=payload[:dlc],
        direction=_direction(values.get("Dir")),
        is_remote=False,
    )


def _skipped_event(mdf, group: _Group) -> NonDataEvent:
    try:
        times = mdf.get_master(group.index, record_offset=0, record_count=1)
        start = float(times[0]) if len(times) and math.isfinite(float(times[0])) else 0.0
    except Exception:  # noqa: BLE001 - the summary must not fail the import
        start = 0.0
    return NonDataEvent(
        round(start, _TIMESTAMP_DECIMALS),
        None,
        "Mf4Skipped",
        f"{group.cycles} records of unsupported group '{group.name}' were not imported",
    )


def _int(value) -> int | None:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number) or number != int(number):
        return None
    return int(number)


def _bus(value) -> str | None:
    number = _int(value)
    return str(number) if number is not None and number >= 0 else None


def _direction(value) -> str | None:
    if isinstance(value, bytes):
        text = value.decode("ascii", "ignore").strip("\0 ").lower()
        return {"rx": "Rx", "tx": "Tx"}.get(text)
    number = _int(value)
    return {0: "Rx", 1: "Tx"}.get(number) if number is not None else None


def _check_cancel(cancel_check: Callable[[], bool] | None) -> None:
    if cancel_check is not None and cancel_check():
        from cantracediag.pipeline import ImportCancelled

        raise ImportCancelled("Import cancelled by operator.")


def _is_cancel(exc: BaseException) -> bool:
    from cantracediag.pipeline import ImportCancelled

    return isinstance(exc, ImportCancelled)


__all__ = ["Mf4ImportError", "Mf4ParseResult", "parse_mf4", "stream_mf4"]
