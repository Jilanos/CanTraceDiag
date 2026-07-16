from pathlib import Path

import pytest

import cantracediag.pipeline as pipeline
from cantracediag.pipeline import ImportCancelled, import_trace
from cantracediag.store import TraceStore

FIX = Path(__file__).parent / "fixtures"


def _store():
    store, result = import_trace(FIX / "sample.asc", [FIX / "sample.dbc"], decode_samples=True)
    return store, result


def test_import_summary() -> None:
    store, result = _store()
    s = result.summary
    assert s["frames"] == 6
    assert s["events"] == 2
    assert s["decoded_frames"] == 5  # all but the unknown extended id
    assert s["unique_ids"] == 3
    store.close()


def test_signal_series_is_time_ordered() -> None:
    store, _ = _store()
    series = store.signal_series("EngineData", "EngineSpeed")
    assert series["t"] == sorted(series["t"])
    assert series["unit"] == "rpm"
    assert len(series["v"]) == len(series["t"]) > 0
    store.close()


def test_nearest_sample_no_interpolation() -> None:
    store, _ = _store()
    # 0.012 sits between samples at 0.010 and 0.020; nearest is 0.010.
    near = store.nearest_sample("EngineData", "EngineSpeed", 0.012)
    assert near["timestamp_s"] == 0.010
    # Returned value is an actual stored sample, never an interpolated one.
    series = store.signal_series("EngineData", "EngineSpeed")
    assert near["value"] in series["v"]
    store.close()


def test_trace_rows_merge_frames_and_events() -> None:
    store, _ = _store()
    page = store.trace_rows(limit=100)
    assert page["total"] == 8
    kinds = {r["kind"] for r in page["rows"]}
    assert kinds == {"frame", "event"}
    times = [r["timestamp_s"] for r in page["rows"]]
    assert times == sorted(times)
    store.close()


def test_trace_rows_pagination() -> None:
    store, _ = _store()
    first = store.trace_rows(offset=0, limit=3)
    second = store.trace_rows(offset=3, limit=3)
    assert len(first["rows"]) == 3
    assert first["rows"][0]["timestamp_s"] <= second["rows"][0]["timestamp_s"]
    store.close()


def test_trace_rows_can_exclude_events() -> None:
    store, _ = _store()
    only_frames = store.trace_rows(limit=100, include_events=False)
    assert all(r["kind"] == "frame" for r in only_frames["rows"])
    assert only_frames["total"] == 6
    store.close()


def test_frame_signals_lookup() -> None:
    store, _ = _store()
    sigs = store.frame_signals(0.0, 0x100)
    names = {s["signal_name"] for s in sigs}
    assert {"EngineSpeed", "EngineTemp"} <= names
    store.close()


def test_trace_rows_filter_by_signal() -> None:
    store, _ = _store()
    page = store.trace_rows(limit=100, signal="EngineSpeed")
    assert page["total"] > 0
    assert all(r["name"] == "EngineData" for r in page["rows"])
    assert store.trace_rows(limit=100, signal="NoSuchSignal")["total"] == 0
    store.close()


def test_import_reports_progress() -> None:
    progress: list[float] = []
    store, _ = import_trace(FIX / "sample.asc", [FIX / "sample.dbc"], on_progress=progress.append)

    assert progress
    assert progress[-1] == 1.0
    assert all(0.0 <= value <= 1.0 for value in progress)
    store.close()


def test_import_defaults_to_lazy_decode_without_materialized_samples() -> None:
    store, result = import_trace(FIX / "sample.asc", [FIX / "sample.dbc"])

    assert result.summary["frames"] == 6
    assert result.summary["decoded_frames"] == 5
    assert store.sample_count() == 0
    page = store.trace_rows(limit=100)
    assert page["total"] == 8
    assert any(row["name"] == "EngineData" for row in page["rows"])
    store.close()


def test_import_cancellation_stops_pipeline() -> None:
    calls = 0

    def cancel_after_first_item() -> bool:
        nonlocal calls
        calls += 1
        return calls > 1

    with pytest.raises(ImportCancelled):
        import_trace(FIX / "sample.asc", [FIX / "sample.dbc"], cancel_check=cancel_after_first_item)


def test_sample_batch_flush_is_bounded_for_multi_signal_frames(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    batch_sizes: list[int] = []
    original = TraceStore.ingest_samples

    def record_ingest(self: TraceStore, samples):
        materialized = list(samples)
        batch_sizes.append(len(materialized))
        return original(self, materialized)

    monkeypatch.setattr(pipeline, "_BATCH", 3)
    monkeypatch.setattr(TraceStore, "ingest_samples", record_ingest)

    store, _ = import_trace(FIX / "sample.asc", [FIX / "sample.dbc"], decode_samples=True)

    assert sum(batch_sizes) == 9
    assert batch_sizes
    assert max(batch_sizes) <= 3
    store.close()
