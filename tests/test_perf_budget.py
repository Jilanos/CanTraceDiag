"""Synthetic time/memory budget for hot paths (task_022, AC16).

These guard against a regression to whole-trace materialization. Budgets are
generous absolute ceilings so they pass on CI across Python 3.11 and 3.12, while
still failing loudly if a query starts scaling with the full trace size.
"""

from __future__ import annotations

import time
import tracemalloc

from cantracediag.models import DecodedSignalSample, RawCanFrame
from cantracediag.store import TraceStore


def _large_store(frames: int = 100_000, samples: int = 100_000) -> TraceStore:
    store = TraceStore()
    store.ingest_frames(
        [RawCanFrame(i / 1000.0, "1", 0x100, False, 1, b"\x01", direction="Rx",
                     message_name="M", decode_status="ok")
         for i in range(frames)]
    )
    store.ingest_samples(
        [DecodedSignalSample(i / 1000.0, "1", 0x100, "M", "Sig", float(i), "u")
         for i in range(samples)]
    )
    return store


def test_paginated_query_is_memory_bounded() -> None:
    store = _large_store()
    tracemalloc.start()
    page = store.trace_rows(limit=200)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    # A page is bounded to its limit regardless of the 100k-row total, and the
    # Python-side peak stays small (no whole-trace materialization).
    assert len(page["rows"]) == 200
    assert page["total"] == 100_000
    assert peak < 8 * 1024 * 1024, f"page query peak too high: {peak} bytes"
    store.close()


def test_series_query_is_point_bounded() -> None:
    store = _large_store()
    series = store.signal_series("M", "Sig", max_points=1000)
    assert series["raw_count"] == 100_000
    assert len(series["t"]) <= 1000  # decimated server-side, never the full series
    store.close()


def test_hot_queries_stay_within_time_budget() -> None:
    store = _large_store()
    start = time.perf_counter()
    for _ in range(20):
        store.trace_rows(limit=200)
        store.signal_series("M", "Sig", max_points=1000)
        store.nearest_sample("M", "Sig", 50.0)
    elapsed = time.perf_counter() - start
    # 20 rounds of the three hottest queries over a 100k-row trace: a generous
    # ceiling that still catches a regression to repeated full scans.
    assert elapsed < 20.0, f"hot-query budget exceeded: {elapsed:.2f}s"
    store.close()
