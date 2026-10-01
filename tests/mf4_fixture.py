"""Byte-level writer for synthetic MDF 4.11 bus-logging fixtures (tests only).

It reproduces the layout of the third-party logger behind the external sample
(see ``logics/external/mf4_sample_inspection.md``): a single data group with
one-byte record IDs whose records from every channel group interleave in one
DT block, a ``CAN_DataFrame`` structure channel per group, and bus number,
direction and IDE flag stored either in the record or as *virtual* channels
whose constant value comes from a linear conversion.

``unfinished=True`` writes what a logger leaves behind when it stops without
finalizing: an ``UnFinMF`` identifier with flags ``0x25``, zero cycle counters
and a last DT block whose length covers only its 24-byte header.

The writer only knows what the tests need; it is not an MDF implementation.
"""

from __future__ import annotations

import struct
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

_MASTER_BYTES = 6  # 48-bit microsecond timestamp, as in the sample


@dataclass
class Group:
    """One channel group. ``kind`` is frame | remote | error | lin."""

    name: str
    record_id: int
    kind: str = "frame"
    # Constant field values stored as virtual channels (e.g. {"BusChannel": 9}).
    constants: dict[str, int] = field(default_factory=dict)
    # Optional per-record fields stored in the record (one byte each).
    stored: tuple[str, ...] = ()
    # Omit a mandatory child channel to model a layout we cannot import.
    omit: tuple[str, ...] = ()

    @property
    def prefix(self) -> str:
        return {
            "frame": "CAN_DataFrame",
            "remote": "CAN_RemoteFrame",
            "error": "CAN_ErrorFrame",
            "lin": "LIN_Frame",
        }[self.kind]

    def fixed_fields(self) -> list[tuple[str, int, int, int]]:
        """(name, byte_offset, bit_count, byte_width) of in-record children."""
        out: list[tuple[str, int, int, int]] = []
        offset = _MASTER_BYTES
        if self.kind != "error":
            out.append(("ID", offset, 32, 4))
            offset += 4
            out.append(("DLC", offset, 4, 1))
            offset += 1
        if self.kind in ("frame", "lin"):
            out.append(("DataLength", offset, 7, 1))
            offset += 1
            out.append(("DataBytes", offset, 64, 8))
            offset += 8
        for name in self.stored:
            out.append((name, offset, 8, 1))
            offset += 1
        return [f for f in out if f[0] not in self.omit]

    @property
    def record_size(self) -> int:
        fields = self.fixed_fields()
        end = max((o + w for _n, o, _b, w in fields), default=_MASTER_BYTES)
        return max(end, _MASTER_BYTES + 1)


@dataclass
class Record:
    group: str
    t: float  # seconds
    id: int = 0
    dlc: int = 0
    data: bytes = b""
    length: int | None = None  # DataLength; defaults to dlc
    values: dict[str, int] = field(default_factory=dict)  # stored fields


class _Blocks:
    def __init__(self) -> None:
        self.buf = bytearray()

    def add(self, block_id: bytes, links: list[int], data: bytes) -> int:
        addr = len(self.buf)
        body = struct.pack(f"<{len(links)}Q", *links) + data
        length = 24 + len(body)
        pad = (-length) % 8
        self.buf += struct.pack("<4s4sQQ", block_id, b"\0" * 4, length + pad, len(links))
        self.buf += body + b"\0" * pad
        return addr

    def patch_link(self, block_addr: int, link_index: int, value: int) -> None:
        struct.pack_into("<Q", self.buf, block_addr + 24 + 8 * link_index, value)

    def text(self, value: str) -> int:
        return self.add(b"##TX", [], value.encode() + b"\0")


def _linear(blocks: _Blocks, offset: float, factor: float) -> int:
    # cc_type 1 (linear): phys = P1 + P2 * raw
    data = struct.pack("<BBHHHdd", 1, 0, 0, 0, 2, 0.0, 0.0) + struct.pack("<dd", offset, factor)
    return blocks.add(b"##CC", [0, 0, 0, 0], data)


def _channel(
    blocks: _Blocks,
    name: str,
    cn_type: int,
    data_type: int,
    byte_offset: int,
    bit_count: int,
    conversion: int = 0,
    sync_type: int = 0,
) -> int:
    name_addr = blocks.text(name)
    data = struct.pack(
        "<BBBBIIIIBBH6d",
        cn_type, sync_type, data_type, 0, byte_offset, bit_count, 0, 0, 0, 0, 0,
        0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
    )
    # links: next, composition, name, source, conversion, data, unit, comment
    return blocks.add(b"##CN", [0, 0, name_addr, 0, conversion, 0, 0, 0], data)


def write_mf4(
    path: str | Path,
    groups: list[Group],
    records: Iterable[Record],
    *,
    unfinished: bool = False,
    truncate: int = 0,
    spoof_signature: bool = False,
) -> Path:
    """Write the fixture and return its path.

    ``truncate`` drops that many trailing bytes (a cut-off recording);
    ``spoof_signature`` overwrites the payload of the first 8-byte-aligned
    DLC-8 frame with a fake ``##TX`` block header.
    """
    path = Path(path)
    blocks = _Blocks()
    blocks.buf += struct.pack(
        "<8s8s8s4sH30sHH",
        b"UnFinMF " if unfinished else b"MDF     ",
        b"4.11    ",
        b"ctdtest ",
        b"\0" * 4,
        411,
        b"\0" * 30,
        0x25 if unfinished else 0,
        0,
    )
    hd = blocks.add(
        b"##HD", [0, 0, 0, 0, 0, 0],
        struct.pack("<QhhBBBBdd", 0, 0, 0, 0, 0, 0, 0, 0.0, 0.0),
    )
    dg = blocks.add(b"##DG", [0, 0, 0, 0], struct.pack("<B7x", 1))
    blocks.patch_link(hd, 0, dg)

    by_name = {g.name: g for g in groups}
    cg_addrs: dict[str, int] = {}
    previous_cg = 0
    for group in groups:
        master_conv = _linear(blocks, 0.0, 1e-6)
        master = _channel(blocks, "Timestamp", 2, 0, 0, 48, master_conv, sync_type=1)
        struct_bits = (group.record_size - _MASTER_BYTES) * 8
        structure = _channel(blocks, group.prefix, 0, 10, _MASTER_BYTES, struct_bits)
        blocks.patch_link(master, 0, structure)
        children: list[int] = []
        for name, offset, bits, _width in group.fixed_fields():
            data_type = 10 if name == "DataBytes" else 0
            children.append(
                _channel(blocks, f"{group.prefix}.{name}", 0, data_type, offset, bits)
            )
        for name, value in group.constants.items():
            conv = _linear(blocks, float(value), 0.0)
            children.append(_channel(blocks, f"{group.prefix}.{name}", 6, 0, 0, 0, conv))
        for left, right in zip(children, children[1:], strict=False):
            blocks.patch_link(left, 0, right)
        if children:
            blocks.patch_link(structure, 1, children[0])
        acq = blocks.text(group.name)
        cg = blocks.add(
            b"##CG", [0, master, acq, 0, 0, 0],
            struct.pack("<QQHHIII", group.record_id, 0, 0, ord("."), 0, group.record_size, 0),
        )
        cg_addrs[group.name] = cg
        if previous_cg:
            blocks.patch_link(previous_cg, 0, cg)
        else:
            blocks.patch_link(dg, 1, cg)
        previous_cg = cg

    # DT last: its data runs to end of file, like the sample.
    dt = blocks.add(b"##DT", [], b"")
    blocks.patch_link(dg, 2, dt)
    counts = {g.name: 0 for g in groups}
    spoofed = not spoof_signature
    with open(path, "wb") as handle:
        handle.write(blocks.buf)
        position = len(blocks.buf)
        for rec in records:
            group = by_name[rec.group]
            body = bytearray(group.record_size)
            body[0:_MASTER_BYTES] = round(rec.t * 1e6).to_bytes(_MASTER_BYTES, "little")
            data = rec.data
            for name, offset, _bits, width in group.fixed_fields():
                if name == "ID":
                    struct.pack_into("<I", body, offset, rec.id)
                elif name == "DLC":
                    body[offset] = rec.dlc & 0x0F
                elif name == "DataLength":
                    body[offset] = rec.dlc if rec.length is None else rec.length
                elif name == "DataBytes":
                    payload_addr = position + 1 + offset
                    if not spoofed and rec.dlc == 8 and payload_addr % 8 == 0:
                        data = b"##TX\0\0\0\0"
                        spoofed = True
                    body[offset:offset + width] = data.ljust(width, b"\0")[:width]
                else:
                    body[offset] = rec.values.get(name, 0)
            chunk = bytes([group.record_id]) + bytes(body)
            handle.write(chunk)
            position += len(chunk)
            counts[rec.group] += 1
        end = position

    with open(path, "r+b") as handle:
        if not unfinished:
            handle.seek(dt + 8)
            handle.write(struct.pack("<Q", end - dt))
            for name, cg in cg_addrs.items():
                handle.seek(cg + 24 + 6 * 8 + 8)  # cycle_count after record_id
                handle.write(struct.pack("<Q", counts[name]))
        if truncate:
            handle.truncate(end - truncate)
    return path
