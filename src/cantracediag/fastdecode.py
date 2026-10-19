"""Vectorized single-signal decoding for the lazy plot path (req_034 AC4).

The first plot of a signal decodes every stored frame of its message. Doing that
frame by frame through cantools costs minutes on a 1 GiB trace, so plain signals
are decoded column-wise with numpy instead. A signal qualifies only when the
result is provably identical to :meth:`Decoder.decode_signal`:

* its message is not multiplexed and the signal is an integer (not IEEE float);
* it is at most 52 bits wide and ``max|raw| * |scale| + |offset|`` stays below
  2**53, so every value cantools computes with Python ints/floats is computed
  with the same exact or identically rounded float64 operations here;
* frames are kept exactly when cantools would decode them: not remote and at
  least as many data bytes as the message length (``allow_truncated=False``).

Anything else returns ``None`` from :func:`plan` and keeps the exact per-frame
path. tests/test_fastdecode.py checks equality against cantools on random
payloads for both byte orders, signedness, odd widths and lengths.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from cantools.database.can import Message

_EXACT = 2.0**53


@dataclass(frozen=True, slots=True)
class Plan:
    big_endian: bool
    shift: int
    mask: int
    length: int
    signed: bool
    scale: float
    offset: float
    min_bytes: int
    identity: bool


def plan(message: Message, signal_name: str) -> Plan | None:
    if message.is_multiplexed():
        return None
    signal = next((s for s in message.signals if s.name == signal_name), None)
    if signal is None or signal.is_float or signal.length > 52 or signal.length < 1:
        return None
    scale, offset = signal.scale, signal.offset
    max_raw = float(2**signal.length - 1)
    if max_raw * abs(scale) + abs(offset) >= _EXACT:
        return None
    if signal.byte_order == "little_endian":
        shift = signal.start
        big = False
    else:
        # Motorola "sawtooth" numbering: ``start`` is the MSB; in the payload
        # read as one big-endian 64-bit word its index from the LSB is below.
        msb = (7 - signal.start // 8) * 8 + signal.start % 8
        shift = msb - signal.length + 1
        big = True
    if shift < 0 or shift + signal.length > 64:
        return None
    return Plan(
        big_endian=big, shift=shift, mask=(1 << signal.length) - 1, length=signal.length,
        signed=signal.is_signed, scale=scale, offset=offset, min_bytes=message.length,
        identity=(scale == 1 and offset == 0),
    )


def decode(p: Plan, data_hex: list[str | None], is_remote: list[bool]) -> tuple[np.ndarray,
                                                                              np.ndarray]:
    """Return ``(keep, values)``: which rows yield a sample, and their float64 values."""
    payloads = [bytes.fromhex(h) if h else b"" for h in data_hex]
    keep = np.fromiter(
        (not r and len(b) >= p.min_bytes for b, r in zip(payloads, is_remote, strict=True)),
        dtype=bool, count=len(payloads),
    )
    words = np.frombuffer(
        b"".join(b[:8].ljust(8, b"\0") for b in payloads),
        dtype=">u8" if p.big_endian else "<u8",
    ).astype(np.uint64)
    raw = ((words >> np.uint64(p.shift)) & np.uint64(p.mask)).astype(np.int64)
    if p.signed:
        sign = np.int64(1 << (p.length - 1))
        raw = np.where(raw & sign, raw - np.int64(1 << p.length), raw)
    values = raw.astype(np.float64)
    if not p.identity:
        values = values * float(p.scale) + float(p.offset)
    return keep, values
