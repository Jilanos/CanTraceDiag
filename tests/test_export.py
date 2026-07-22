"""Tests for the diagnostic report, range statistics and exports (task_017).

Covers AC1 (report synthesis), AC2 (streamed CSV/Parquet export with bounded
memory) and AC3 (per-signal range statistics).
"""

from __future__ import annotations

import io
import tracemalloc
from pathlib import Path

import pyarrow.parquet as pq
import pytest
from starlette.testclient import TestClient

from cantracediag import export
from cantracediag.models import DecodedSignalSample
from cantracediag.store import TraceStore

FIX = Path(__file__).parent / "fixtures"


def _import_sample(client: TestClient) -> None:
    r = client.post(
        "/api/import",
        json={"trace_path": str(FIX / "sample.asc"),
              "dbc_paths": [str(FIX / "sample.dbc")]},
    )
    assert r.status_code == 200


def _numeric_store(values: list[float]) -> TraceStore:
    store = TraceStore()
    store.ingest_samples(
        [
            DecodedSignalSample(i / 100.0, "1", 0x100, "M", "Sig", v, "rpm")
            for i, v in enumerate(values)
        ]
    )
    return store


def _text_store(values: list[str]) -> TraceStore:
    store = TraceStore()
    store.ingest_samples(
        [
            DecodedSignalSample(i / 100.0, "1", 0x100, "M", "Gear", v, None)
            for i, v in enumerate(values)
        ]
    )
    return store


# -- range statistics (AC3) -----------------------------------------------


def test_signal_stats_numeric() -> None:
    store = _numeric_store([0.0, 10.0, 20.0, 30.0])
    stats = store.signal_stats("M", "Sig")
    assert stats["kind"] == "numeric"
    assert stats["count"] == 4
    assert stats["min"] == 0.0
    assert stats["max"] == 30.0
    assert stats["mean"] == pytest.approx(15.0)
    assert stats["std"] == pytest.approx(12.909944, rel=1e-4)
    assert stats["rms"] == pytest.approx(18.708287, rel=1e-4)
    assert stats["unit"] == "rpm"
    store.close()


def test_signal_stats_window_bounds() -> None:
    store = _numeric_store([0.0, 10.0, 20.0, 30.0])  # timestamps 0.00..0.03
    stats = store.signal_stats("M", "Sig", start_s=0.01, end_s=0.02)
    assert stats["count"] == 2
    assert stats["min"] == 10.0
    assert stats["max"] == 20.0
    store.close()


def test_signal_stats_text_distribution() -> None:
    store = _text_store(["D", "D", "N", "R", "D"])
    stats = store.signal_stats("M", "Gear")
    assert stats["kind"] == "text"
    assert stats["count"] == 5
    # Most frequent value first.
    assert stats["distribution"][0] == {"value": "D", "count": 3}
    assert {d["value"] for d in stats["distribution"]} == {"D", "N", "R"}
    store.close()


def test_signal_stats_empty_window_is_explicit() -> None:
    store = _numeric_store([0.0, 10.0])
    stats = store.signal_stats("M", "Sig", start_s=100.0, end_s=200.0)
    assert stats["kind"] == "empty"
    assert stats["count"] == 0
    store.close()


def test_signal_stats_endpoint(client: TestClient) -> None:
    _import_sample(client)
    r = client.get(
        "/api/signal-stats",
        params={"message": "EngineData", "signal": "EngineSpeed"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["kind"] == "numeric"
    assert body["count"] >= 1
    assert body["unit"] == "rpm"
    assert body["max"] >= body["min"]


# -- report synthesis (AC1) -----------------------------------------------


def test_report_endpoint(client: TestClient) -> None:
    _import_sample(client)
    r = client.get("/api/report")
    assert r.status_code == 200
    body = r.json()
    assert body["trace_path"].endswith("sample.asc")
    assert body["frames"] >= 1
    assert body["events"] >= 1
    assert body["unique_ids"] >= 1
    assert body["duration_s"] == pytest.approx(body["end_s"] - body["start_s"])
    # sample.dbc decodes EngineData/VehicleState frames, so it is credited.
    assert any(u["source"] == "sample.dbc" for u in body["dbcs_used"])
    # 0x7FF is unknown to the DBC; the ErrorFrame is a non-data ASC event.
    assert body["anomalies"]["unknown_id"] >= 1
    assert body["anomalies"]["asc_events"].get("ErrorFrame", 0) >= 1


def test_report_requires_loaded_trace(client: TestClient) -> None:
    assert client.get("/api/report").status_code == 409


# -- exports (AC2) --------------------------------------------------------


def test_export_batches_are_memory_bounded() -> None:
    """The resident batch never exceeds ``batch_size`` regardless of total rows.

    This is the core AC2 property: peak memory is a function of the batch size,
    not of the number of exported rows.
    """
    n = 200_000
    store = _numeric_store([float(i) for i in range(n)])
    batch_size = 4096
    max_batch = 0
    total = 0
    for batch in store.iter_export_batches([("M", "Sig")], batch_size=batch_size):
        max_batch = max(max_batch, batch.num_rows)
        total += batch.num_rows
    assert total == n
    assert max_batch <= batch_size
    store.close()


def test_export_csv_formatter_peak_is_flat() -> None:
    """Formatting 100x more rows must not scale the formatter's peak memory."""

    def consume(n: int) -> tuple[int, int]:
        store = _numeric_store([float(i) for i in range(n)])
        tracemalloc.start()
        emitted = 0
        for chunk in export.long_csv(
            store.iter_export_batches([("M", "Sig")], batch_size=2048)
        ):
            emitted += len(chunk)  # discard immediately, never accumulate
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        store.close()
        return peak, emitted

    peak_small, bytes_small = consume(2_000)
    peak_big, bytes_big = consume(200_000)
    # All rows really were exported (payload scales with row count)...
    assert bytes_big > bytes_small * 50
    # ...but the streaming formatter's peak stays flat, not proportional to N.
    assert peak_big < peak_small * 4
    assert peak_big < bytes_big


def test_export_long_csv_content() -> None:
    store = _numeric_store([1.0, 2.0])
    chunks = b"".join(export.long_csv(store.iter_export_batches([("M", "Sig")])))
    text = chunks.decode("utf-8")
    lines = text.strip().splitlines()
    assert lines[0] == "timestamp_s,message,signal,value,unit"
    assert len(lines) == 3
    assert lines[1].startswith("0.0,M,Sig,1.0,rpm")
    store.close()


def test_export_long_parquet_roundtrip() -> None:
    store = _numeric_store([1.0, 2.0, 3.0])
    sink = io.BytesIO()
    export.long_parquet(store.iter_export_batches([("M", "Sig")]), sink)
    sink.seek(0)
    table = pq.read_table(sink)
    assert table.num_rows == 3
    assert table.column_names == list(export.LONG_COLUMNS)
    store.close()


def test_export_empty_parquet_has_schema() -> None:
    store = _numeric_store([1.0])
    sink = io.BytesIO()
    # No matching signal -> a valid, empty Parquet carrying the canonical schema.
    export.long_parquet(store.iter_export_batches([("M", "Missing")]), sink)
    sink.seek(0)
    table = pq.read_table(sink)
    assert table.num_rows == 0
    assert table.column_names == list(export.LONG_COLUMNS)
    store.close()


def test_export_wide_csv_does_not_interpolate() -> None:
    store = TraceStore()
    # Two signals sampled at partly disjoint timestamps.
    store.ingest_samples(
        [
            DecodedSignalSample(0.0, "1", 0x100, "M", "A", 1.0, "u"),
            DecodedSignalSample(0.0, "1", 0x100, "M", "B", 9.0, "u"),
            DecodedSignalSample(0.1, "1", 0x100, "M", "A", 2.0, "u"),
        ]
    )
    labels = [export.signal_label("M", "A"), export.signal_label("M", "B")]
    text = b"".join(
        export.wide_csv(
            store.iter_export_batches([("M", "A"), ("M", "B")]), labels
        )
    ).decode("utf-8")
    lines = text.strip().splitlines()
    assert lines[0] == "timestamp_s,M.A,M.B"
    # At 0.1, B has no sample: its cell is empty, not interpolated.
    assert lines[2] == "0.1,2.0,"
    store.close()


def test_export_csv_wide_endpoint(client: TestClient) -> None:
    _import_sample(client)
    r = client.post(
        "/api/export",
        json={
            "signals": [{"message": "EngineData", "signal": "EngineSpeed"}],
            "scope": "full",
            "format": "csv_wide",
        },
    )
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/csv")
    text = r.content.decode("utf-8")
    assert text.splitlines()[0].startswith("timestamp_s,EngineData.EngineSpeed")
    assert "rpm" not in text.splitlines()[0]


def test_export_endpoint_csv(client: TestClient) -> None:
    _import_sample(client)
    r = client.post(
        "/api/export",
        json={
            "signals": [{"message": "EngineData", "signal": "EngineSpeed"}],
            "scope": "full",
            "format": "csv",
        },
    )
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/csv")
    lines = r.text.strip().splitlines()
    assert lines[0] == "timestamp_s,message,signal,value,unit"
    assert len(lines) > 1


def test_export_endpoint_parquet(client: TestClient) -> None:
    _import_sample(client)
    r = client.post(
        "/api/export",
        json={
            "signals": [{"message": "EngineData", "signal": "EngineSpeed"}],
            "scope": "full",
            "format": "parquet",
        },
    )
    assert r.status_code == 200
    table = pq.read_table(io.BytesIO(r.content))
    assert table.column_names == list(export.LONG_COLUMNS)
    assert table.num_rows > 0


def test_export_between_ab_requires_bounds(client: TestClient) -> None:
    _import_sample(client)
    r = client.post(
        "/api/export",
        json={
            "signals": [{"message": "EngineData", "signal": "EngineSpeed"}],
            "scope": "between_ab",
            "format": "csv",
        },
    )
    assert r.status_code == 400


def test_export_rejects_empty_selection(client: TestClient) -> None:
    _import_sample(client)
    r = client.post("/api/export", json={"signals": [], "scope": "full"})
    assert r.status_code == 400
