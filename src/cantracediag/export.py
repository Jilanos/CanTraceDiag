"""Streaming exports: decoded signal samples (CSV/Parquet) and raw frames (ASC).

Exports never materialize the whole result set in memory. The store yields
decoded samples one bounded record batch at a time (see
:meth:`TraceStore.iter_export_batches`), and each formatter here consumes those
batches incrementally, so peak memory stays a function of the batch size rather
than of the total number of exported rows. A synthetic test proves that
property (see ``tests/test_export.py``).

Two shapes are offered:

* *long* — the canonical schema ``(timestamp_s, message, signal, value, unit)``,
  one physical sample per row, available as CSV and Parquet.
* *wide* — an optional CSV that aligns samples by timestamp, one column per
  selected signal. It never interpolates: a cell is empty when that signal has
  no sample at that exact timestamp.

The raw *ASC* export (:func:`raw_asc`) is a separate contract: it serializes
stored raw CAN frames, not decoded samples, so it needs neither a DBC nor a
signal selection. See its docstring for the line grammar and policies.
"""

from __future__ import annotations

import csv
import io
import math
from collections.abc import Iterable, Iterator
from datetime import datetime

import pyarrow as pa
import pyarrow.parquet as pq

# Canonical long-format column order, shared by CSV and Parquet.
LONG_COLUMNS = ("timestamp_s", "message", "signal", "value", "unit")

# Fixed schema used to emit a valid, empty Parquet file when the selection has
# no samples (there is then no batch to infer a schema from).
LONG_SCHEMA = pa.schema(
    [
        ("timestamp_s", pa.float64()),
        ("message", pa.string()),
        ("signal", pa.string()),
        ("value", pa.string()),
        ("unit", pa.string()),
    ]
)


def signal_label(message: str, signal: str) -> str:
    """Stable ``message.signal`` label used for wide-format column headers."""
    return f"{message}.{signal}"


def _drain(buf: io.StringIO) -> bytes:
    """Return the buffered text as UTF-8 bytes and reset the buffer."""
    data = buf.getvalue()
    buf.seek(0)
    buf.truncate(0)
    return data.encode("utf-8")


def long_csv(batches: Iterable[pa.RecordBatch]) -> Iterator[bytes]:
    """Yield the long-format export as UTF-8 CSV, one chunk per batch."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(LONG_COLUMNS)
    yield _drain(buf)
    for batch in batches:
        cols = batch.to_pydict()
        columns = [cols[name] for name in LONG_COLUMNS]
        for row in zip(*columns, strict=True):
            writer.writerow(["" if value is None else value for value in row])
        chunk = _drain(buf)
        if chunk:
            yield chunk


def long_parquet(batches: Iterable[pa.RecordBatch], sink) -> None:
    """Write the long-format export to ``sink`` as Parquet, batch by batch.

    The :class:`~pyarrow.parquet.ParquetWriter` flushes row groups as batches
    arrive, so only one batch is resident at a time. An empty selection still
    produces a valid Parquet file carrying the canonical schema.
    """
    writer: pq.ParquetWriter | None = None
    try:
        for batch in batches:
            if writer is None:
                writer = pq.ParquetWriter(sink, batch.schema)
            writer.write_batch(batch)
        if writer is None:
            writer = pq.ParquetWriter(sink, LONG_SCHEMA)
    finally:
        if writer is not None:
            writer.close()


def wide_csv(batches: Iterable[pa.RecordBatch], labels: list[str]) -> Iterator[bytes]:
    """Yield a wide CSV aligning samples by timestamp, one column per signal.

    Batches must arrive ordered by ``(timestamp_s, message, signal)`` so that
    all samples sharing a timestamp are contiguous; only the row currently being
    assembled is held in memory. Missing values stay empty (no interpolation).
    """
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["timestamp_s", *labels])
    yield _drain(buf)

    index = {label: i for i, label in enumerate(labels)}
    current_ts: float | None = None
    row = [""] * len(labels)

    for batch in batches:
        cols = batch.to_pydict()
        stream = zip(
            cols["timestamp_s"], cols["message"], cols["signal"], cols["value"],
            strict=True,
        )
        for ts, message, signal, value in stream:
            if current_ts is not None and ts != current_ts:
                writer.writerow([current_ts, *row])
                row = [""] * len(labels)
            current_ts = ts
            slot = index.get(signal_label(message, signal))
            if slot is not None:
                row[slot] = "" if value is None else value
        chunk = _drain(buf)
        if chunk:
            yield chunk

    if current_ts is not None:
        writer.writerow([current_ts, *row])
        yield _drain(buf)


# -- raw ASC trace export ----------------------------------------------------

# Six fractional digits: a re-import differs from the stored timestamp by at
# most 0.5 us, inside the documented 1 us round-trip tolerance.
ASC_TIME_DECIMALS = 6

# Explicit policies for frames whose bus channel or direction is unknown. ASC
# lines require both, so "block" refuses the export instead of inventing them;
# "assume" writes channel 1 / Rx and says so in the header.
PROVENANCE_POLICIES = ("block", "assume")
ASSUMED_CHANNEL = "1"
ASSUMED_DIRECTION = "Rx"


class ProvenanceError(ValueError):
    """A frame lacks channel/direction and the policy forbids assuming them."""


def asc_header_lines(
    summary: dict,
    *,
    source: str | None,
    scope: str,
    start_s: float | None,
    end_s: float | None,
    policy: str,
    warnings: Iterable[str] = (),
    now: datetime | None = None,
) -> list[str]:
    """Header and disclosure comments for a raw ASC export."""
    moment = now or datetime.now()
    stamp = moment.strftime("%a %b %d %I:%M:%S.000 ") + moment.strftime("%p").lower()
    stamp += moment.strftime(" %Y")
    lines = [
        f"date {stamp}",
        "base hex  timestamps absolute",
        "no internal events logged",
        "// CanTraceDiag raw CAN trace export (classic CAN data/remote frames)",
        "// date above is the export time; timestamps keep the source's relative origin",
    ]
    if source:
        lines.append(f"// source: {_comment(source)}")
    if scope == "full":
        lines.append("// scope: full trace")
    else:
        lines.append(
            f"// scope: {scope} {_fmt_time(start_s)} .. {_fmt_time(end_s)} s (inclusive)"
        )
    lines.append(f"// frames: {summary.get('frames', 0)}")
    excluded = dict(summary.get("excluded_events") or {})
    if summary.get("nonfinite_frames"):
        excluded["non-finite timestamp frames"] = summary["nonfinite_frames"]
    if excluded:
        listed = ", ".join(f"{k}={v}" for k, v in sorted(excluded.items()))
        lines.append(f"// excluded (not written as frames): {listed}")
    else:
        lines.append("// excluded (not written as frames): none")
    unknown_ch = summary.get("unknown_channel", 0)
    unknown_dir = summary.get("unknown_direction", 0)
    if policy == "assume" and (unknown_ch or unknown_dir):
        lines.append(
            f"// ASSUMED provenance: {unknown_ch} frame(s) without a numeric channel written "
            f"on channel {ASSUMED_CHANNEL}, {unknown_dir} frame(s) without a direction "
            f"written as {ASSUMED_DIRECTION}"
        )
    for warning in warnings:
        lines.append(f"// warning: {_comment(warning)}")
    lines.append("Begin Triggerblock")
    return lines


def raw_asc(
    batches: Iterable[dict],
    header: list[str],
    policy: str = "block",
) -> Iterator[bytes]:
    """Yield a Vector-style ASC trace, one chunk per batch of stored frames.

    Line grammar, matching the project ASC reader and Vector tooling::

        <time> <channel> <id>[x] <Rx|Tx> d <dlc> <byte> ...
        <time> <channel> <id>[x] <Rx|Tx> r <dlc>

    ``time`` keeps the stored relative timestamp with six decimals, ``channel``
    is the original numeric bus number (sparse numbers are kept), ``id`` is
    upper-case hex with an ``x`` suffix for extended identifiers, and payload
    bytes are two-digit hex. Batches must already be ordered by
    ``(timestamp_s, seq)`` (see :meth:`TraceStore.iter_raw_frames`).
    """
    if policy not in PROVENANCE_POLICIES:
        raise ValueError(f"Unknown provenance policy: {policy}")
    yield ("\n".join(header) + "\n").encode("ascii", "replace")
    for batch in batches:
        lines = []
        stream = zip(
            batch["timestamp_s"], batch["channel"], batch["arbitration_id"],
            batch["is_extended_id"], batch["dlc"], batch["data_hex"],
            batch["direction"], batch["is_remote"],
            strict=True,
        )
        for ts, channel, arb_id, extended, dlc, data_hex, direction, remote in stream:
            lines.append(
                asc_frame_line(
                    ts, channel, arb_id, extended, dlc, data_hex, direction, remote, policy
                )
            )
        if lines:
            yield ("\n".join(lines) + "\n").encode("ascii")
    yield b"End TriggerBlock\n"


def asc_frame_line(
    timestamp_s: float,
    channel: str | None,
    arbitration_id: int,
    is_extended_id: bool,
    dlc: int,
    data_hex: str | None,
    direction: str | None,
    is_remote: bool,
    policy: str = "block",
) -> str:
    """Serialize one stored frame as an ASC line (see :func:`raw_asc`)."""
    if not math.isfinite(timestamp_s):
        raise ValueError("Non-finite timestamp cannot be written to ASC.")
    if channel is None or not str(channel).isdigit():
        if policy != "assume":
            raise ProvenanceError("A frame has no numeric bus channel.")
        channel = ASSUMED_CHANNEL
    if direction not in ("Rx", "Tx"):
        if policy != "assume":
            raise ProvenanceError("A frame has no Rx/Tx direction.")
        direction = ASSUMED_DIRECTION
    ident = f"{int(arbitration_id):X}" + ("x" if is_extended_id else "")
    head = f"{timestamp_s:.{ASC_TIME_DECIMALS}f} {int(channel)}  {ident:<15} {direction}"
    if is_remote:
        return f"{head}   r {int(dlc)}"
    payload = (data_hex or "").split()
    if len(payload) != int(dlc):
        raise ValueError("Stored payload length does not match its DLC.")
    return f"{head}   d {int(dlc)}" + "".join(f" {b}" for b in payload)


def _fmt_time(value: float | None) -> str:
    return "?" if value is None else f"{value:.{ASC_TIME_DECIMALS}f}"


def _comment(text: str) -> str:
    """Single-line, ASCII-safe text for an ASC ``//`` comment."""
    return " ".join(str(text).split()).encode("ascii", "replace").decode("ascii")
