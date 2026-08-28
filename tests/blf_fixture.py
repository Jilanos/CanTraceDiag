"""Deterministic BLF fixtures generated from source.

Real BLF recordings are large binary acquisitions and stay out of the
repository (ADR 0002), so the BLF tests build the bytes they need on the fly.
Every helper here is deterministic: the same call always produces the same
file, which is what makes exact assertions on timestamps and payloads possible.

The valid objects are written with ``python-can``'s ``BLFWriter``. The invalid
ones cannot be, precisely because that writer refuses to emit them; those are
produced by writing an *uncompressed* container and then patching the offending
field in place, which is why :func:`write_anomaly_blf` disables compression.
"""

from __future__ import annotations

from pathlib import Path

import can
from can.io.blf import CAN_MSG_STRUCT, BLFWriter

# Arbitration ids shared with ``sample.dbc`` so a BLF import exercises the real
# decoder rather than a synthetic one.
ENGINE_DATA_ID = 0x100
VEHICLE_STATE_ID = 0x200
EXTENDED_ID = 0x1ABCDEF


def write_sample_blf(path: str | Path) -> Path:
    """Write the representative supported-subset fixture.

    Covers, in file order: a standard-id frame, a second frame sharing that
    timestamp (so ordering has a tie to break), an extended-id frame on a second
    channel with ``Tx`` direction, a zero-DLC frame, and the three object kinds
    that must become diagnostics rather than frames -- a remote request, an
    error frame, and a CAN FD object.
    """
    return _write(
        path,
        [
            _frame(0.000000, ENGINE_DATA_ID, 8, bytes([0x00, 0x10, 0x64, 0, 0, 0, 0, 0])),
            _frame(0.000000, VEHICLE_STATE_ID, 2, bytes([0x10, 0x27])),
            _frame(0.001000, EXTENDED_ID, 3, b"\x01\x02\x03", channel=1, is_rx=False,
                   extended=True),
            _frame(0.002000, VEHICLE_STATE_ID, 0, b""),
            can.Message(timestamp=0.003000, arbitration_id=0x300, is_extended_id=False,
                        dlc=8, data=b"", is_remote_frame=True, channel=0),
            can.Message(timestamp=0.004000, arbitration_id=0x000, is_extended_id=False,
                        is_error_frame=True, channel=0),
            can.Message(timestamp=0.005000, arbitration_id=0x400, is_extended_id=False,
                        dlc=16, data=bytes(16), is_fd=True, channel=0),
        ],
    )


def write_anomaly_blf(path: str | Path) -> Path:
    """Write a fixture whose second object declares an impossible classic DLC.

    The first object stays valid, which is what proves a per-object anomaly does
    not contaminate the frames around it.
    """
    payload = bytes(range(8))
    _write(
        path,
        [
            _frame(0.000000, ENGINE_DATA_ID, 8, bytes(8)),
            _frame(0.001000, 0x7AA, 8, payload),
        ],
        compression_level=0,
    )
    target = Path(path)
    raw = target.read_bytes()
    # channel is 1-based on the wire, flags 0, then the DLC byte we overwrite.
    valid = CAN_MSG_STRUCT.pack(1, 0, 8, 0x7AA, payload)
    broken = CAN_MSG_STRUCT.pack(1, 0, 9, 0x7AA, payload)
    if valid not in raw:
        raise AssertionError("uncompressed CAN message object not found in fixture")
    target.write_bytes(raw.replace(valid, broken))
    return target


def write_corrupt_blf(path: str | Path) -> Path:
    """Write a fixture whose object stream desynchronizes after a valid frame."""
    _write(
        path,
        [
            _frame(0.000000, ENGINE_DATA_ID, 8, bytes(8)),
            _frame(0.001000, VEHICLE_STATE_ID, 2, b"\x10\x27"),
        ],
        compression_level=0,
    )
    target = Path(path)
    raw = target.read_bytes()
    # The first "LOBJ" is the log container itself; break the object signature
    # inside it so the container opens but its contents cannot be walked.
    first = raw.index(b"LOBJ")
    second = raw.index(b"LOBJ", first + 4)
    target.write_bytes(raw[:second] + b"XXXX" + raw[second + 4:])
    return target


def write_non_blf_bytes(path: str | Path) -> Path:
    """Write bytes that are not a BLF container at all."""
    target = Path(path)
    target.write_bytes(b"NOTALOGG" + bytes(32))
    return target


def write_bulk_blf(path: str | Path, count: int) -> Path:
    """Write ``count`` valid standard-id frames, one millisecond apart."""
    return _write(
        path,
        [
            _frame(i / 1000, ENGINE_DATA_ID, 8, bytes([i % 256, 0x10, 0x64, 0, 0, 0, 0, 0]))
            for i in range(count)
        ],
    )


def _frame(
    timestamp: float,
    arbitration_id: int,
    dlc: int,
    data: bytes,
    channel: int = 0,
    is_rx: bool = True,
    extended: bool = False,
) -> can.Message:
    return can.Message(
        timestamp=timestamp,
        arbitration_id=arbitration_id,
        is_extended_id=extended,
        dlc=dlc,
        data=data,
        channel=channel,
        is_rx=is_rx,
    )


def _write(
    path: str | Path, messages: list[can.Message], compression_level: int = -1
) -> Path:
    writer = BLFWriter(str(path), compression_level=compression_level)
    try:
        for message in messages:
            writer.on_message_received(message)
    finally:
        writer.stop()
    return Path(path)
