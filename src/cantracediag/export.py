"""Streaming CSV/Parquet export of decoded signal samples (AC2).

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
"""

from __future__ import annotations

import csv
import io
from collections.abc import Iterable, Iterator

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
