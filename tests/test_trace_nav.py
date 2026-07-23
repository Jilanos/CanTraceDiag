"""Tests for bounded hot endpoints and deterministic trace navigation (task_018).

Covers AC8 (bounded nearest lookups plus a batch cursor endpoint, guarded by a
query-plan benchmark) and AC9 (canonical (timestamp_s, seq) order with opaque
keyset pagination that never duplicates or omits a row, and a locate that opens
the page containing exactly the returned row).
"""

from __future__ import annotations

from pathlib import Path

import pytest
from starlette.testclient import TestClient

from cantracediag.models import DecodedSignalSample
from cantracediag.pipeline import import_trace
from cantracediag.store import TraceStore

FIX = Path(__file__).parent / "fixtures"


def _same_ts_store() -> TraceStore:
    store, _ = import_trace(FIX / "same_timestamp.asc", [FIX / "sample.dbc"])
    return store


def _key(row: dict) -> tuple[float, int]:
    return (row["timestamp_s"], row["seq"])


def _drain_all(store: TraceStore, limit: int) -> list[dict]:
    """Page forward through the whole trace following next_cursor."""
    rows: list[dict] = []
    page = store.trace_rows(limit=limit)
    rows.extend(page["rows"])
    guard = 0
    while page["next_cursor"] is not None:
        guard += 1
        assert guard < 1000, "pagination did not terminate"
        page = store.trace_rows(cursor=page["next_cursor"], limit=limit)
        rows.extend(page["rows"])
    return rows


# -- deterministic pagination (AC9) ---------------------------------------


def test_same_timestamp_pagination_has_no_duplicate_or_omission() -> None:
    store = _same_ts_store()
    total = store.trace_rows(limit=1000)["total"]
    assert total == 9  # 6 frames + 3 events, five of them at t=0.1

    keys = [_key(r) for r in _drain_all(store, limit=2)]
    # Every row surfaced exactly once, none skipped.
    assert len(keys) == total
    assert len(set(keys)) == total
    # Canonical (timestamp_s, seq) order across page boundaries.
    assert keys == sorted(keys)
    store.close()


def test_same_timestamp_rows_are_totally_ordered_by_seq() -> None:
    store = _same_ts_store()
    rows = store.trace_rows(limit=1000)["rows"]
    at_tenth = [r for r in rows if r["timestamp_s"] == pytest.approx(0.1)]
    # The five rows sharing t=0.1 keep a stable, gap-free file order via seq.
    assert len(at_tenth) == 5
    seqs = [r["seq"] for r in at_tenth]
    assert seqs == sorted(seqs)
    assert len(set(seqs)) == 5
    store.close()


def test_prev_cursor_round_trips_to_the_same_page() -> None:
    store = _same_ts_store()
    first = store.trace_rows(limit=3)
    second = store.trace_rows(cursor=first["next_cursor"], limit=3)
    back = store.trace_rows(cursor=second["prev_cursor"], limit=3)
    assert [_key(r) for r in back["rows"]] == [_key(r) for r in first["rows"]]
    store.close()


def test_locate_opens_page_starting_on_the_located_row() -> None:
    store = _same_ts_store()
    loc = store.locate_row(0.18)  # nearest is the first row at t=0.2
    assert loc["cursor"] is not None
    page = store.trace_rows(cursor=loc["cursor"], limit=3)
    # The located row is exactly the first row of the opened page (AC9).
    assert _key(page["rows"][0]) == (loc["timestamp_s"], loc["seq"])
    assert page["start_index"] == loc["index"]
    store.close()


def test_locate_coherent_across_same_timestamp_rows() -> None:
    store = _same_ts_store()
    # A locate at t=0.1 must resolve to one specific row and open on it, even
    # though five rows share that timestamp.
    loc = store.locate_row(0.1)
    assert loc["timestamp_s"] == pytest.approx(0.1)
    page = store.trace_rows(cursor=loc["cursor"], limit=1)
    assert _key(page["rows"][0]) == (loc["timestamp_s"], loc["seq"])
    store.close()


def test_trace_endpoint_rejects_malformed_cursor(client: TestClient) -> None:
    client.post(
        "/api/import",
        json={"trace_path": str(FIX / "same_timestamp.asc"),
              "dbc_paths": [str(FIX / "sample.dbc")]},
    )
    assert client.get("/api/trace", params={"cursor": "not-a-cursor"}).status_code == 400


def test_trace_signal_filter_without_catalog_match_returns_no_rows(client: TestClient) -> None:
    client.post(
        "/api/import",
        json={"trace_path": str(FIX / "sample.asc"),
              "dbc_paths": [str(FIX / "sample.dbc")]},
    )
    r = client.get("/api/trace", params={"signal": "DefinitelyMissingSignal"})
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 0
    assert body["rows"] == []


# -- bounded nearest lookups + batch endpoint (AC8) -----------------------


def _numeric_store(n: int) -> TraceStore:
    store = TraceStore()
    store.ingest_samples(
        [DecodedSignalSample(i / 1000.0, "1", 0x100, "M", "Sig", float(i), "rpm")
         for i in range(n)]
    )
    return store


def test_nearest_sample_is_correct_at_edges_and_midpoints() -> None:
    store = _numeric_store(10)  # timestamps 0.000 .. 0.009
    assert store.nearest_sample("M", "Sig", -1.0)["timestamp_s"] == 0.0   # before first
    assert store.nearest_sample("M", "Sig", 99.0)["timestamp_s"] == 0.009  # after last
    assert store.nearest_sample("M", "Sig", 0.0032)["timestamp_s"] == 0.003
    assert store.nearest_sample("M", "Sig", 0.005)["timestamp_s"] == 0.005  # exact
    store.close()


def _capture_sql(store: TraceStore, monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Record every SQL statement the store issues (its query helpers all funnel
    through ``_one``/``_all``/``_df``)."""
    calls: list[str] = []

    for name in ("_one", "_all", "_df"):
        original = getattr(store, name)

        def recording(sql, params=(), *, _orig=original):
            calls.append(sql)
            return _orig(sql, params)

        monkeypatch.setattr(store, name, recording)
    return calls


def test_nearest_sample_plan_stays_two_bounded_queries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Benchmark guard (AC8): the nearest lookup issues a constant, bounded
    number of queries and never a full distance sort, regardless of trace size."""
    counts = []
    for n in (1_000, 100_000):
        store = _numeric_store(n)
        calls = _capture_sql(store, monkeypatch)
        store.nearest_sample("M", "Sig", n / 2 / 1000.0)
        # Exactly one bounded query before and one after — no scaling with n.
        assert len(calls) == 2
        assert all("LIMIT 1" in sql for sql in calls)
        assert any("<= ?" in sql for sql in calls)
        assert any(">= ?" in sql for sql in calls)
        # Never a sort by absolute distance over every row (the old full scan).
        assert not any("abs(" in sql.lower() for sql in calls)
        counts.append(len(calls))
        store.close()
    # Query count is constant across a 100x size increase (bounded, not linear).
    assert counts[0] == counts[1]


def test_cursors_batch_endpoint_returns_a_and_b(client: TestClient) -> None:
    client.post(
        "/api/import",
        json={"trace_path": str(FIX / "sample.asc"),
              "dbc_paths": [str(FIX / "sample.dbc")]},
    )
    r = client.post(
        "/api/cursors",
        json={
            "signals": [
                {"message": "EngineData", "signal": "EngineSpeed"},
                {"message": "EngineData", "signal": "EngineTemp"},
            ],
            "a": 0.0,
            "b": 0.05,
        },
    )
    assert r.status_code == 200
    body = r.json()
    # N signals for both A and B in a single call.
    assert set(body["a"]) == {"EngineData.EngineSpeed", "EngineData.EngineTemp"}
    assert set(body["b"]) == {"EngineData.EngineSpeed", "EngineData.EngineTemp"}
    assert body["a"]["EngineData.EngineSpeed"]["timestamp_s"] == 0.0


def test_cursors_batch_omits_absent_cursor(client: TestClient) -> None:
    client.post(
        "/api/import",
        json={"trace_path": str(FIX / "sample.asc"),
              "dbc_paths": [str(FIX / "sample.dbc")]},
    )
    r = client.post(
        "/api/cursors",
        json={"signals": [{"message": "EngineData", "signal": "EngineSpeed"}], "a": 0.0},
    )
    assert r.status_code == 200
    assert r.json()["b"] == {}
