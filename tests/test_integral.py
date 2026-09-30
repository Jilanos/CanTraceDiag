"""Signed trapezoidal cursor integral (req_032 AC3/AC6, item_054).

The shared fixture file is also consumed by the PWA engine's test so both
engines are held to identical results.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from starlette.testclient import TestClient

from cantracediag.integral import integral_unit, integrate
from cantracediag.models import DecodedSignalSample
from cantracediag.store import TraceStore

FIX = Path(__file__).parent / "fixtures"
CASES = json.loads((FIX / "integral_cases.json").read_text())["cases"]


def _value(raw: object) -> object:
    if isinstance(raw, dict):
        return float(raw["nonfinite"])
    return raw


def _store(samples: list, unit: str | None) -> TraceStore:
    store = TraceStore()
    store.ingest_samples([
        DecodedSignalSample(float(t), "1", 0x100, "M", "Sig", _value(v), unit or None)
        for t, v in samples
    ])
    return store


def _check(result: dict, case: dict) -> None:
    expect = case["expect"]
    assert result["available"] is expect["available"], (case["name"], result)
    assert result["method"] == "trapezoidal"
    assert result["start_s"] == min(case["a"], case["b"])
    assert result["end_s"] == max(case["a"], case["b"])
    if expect["available"]:
        assert result["integral"] == pytest.approx(expect["integral"], abs=1e-12)
        assert result["reason"] is None
    else:
        assert result["integral"] is None
        assert result["reason"] == expect["reason"]
    if "unit" in expect:
        assert result["unit"] == expect["unit"]


@pytest.mark.parametrize("case", CASES, ids=[c["name"] for c in CASES])
def test_pure_engine_matches_shared_fixtures(case: dict) -> None:
    rows = [(float(t), _value(v)) for t, v in case["samples"]]
    _check(integrate(rows, case["a"], case["b"], case["unit"]), case)


@pytest.mark.parametrize("case", CASES, ids=[c["name"] for c in CASES])
def test_store_matches_shared_fixtures(case: dict) -> None:
    store = _store(case["samples"], case["unit"])
    result = store.signal_integral("M", "Sig", case["a"], case["b"])
    _check(result, case)
    assert result["signal_name"] == "Sig"


def test_integral_unit_semantics() -> None:
    assert integral_unit("A") == "A·s"
    assert integral_unit("") == "s"
    assert integral_unit(None) == "s"
    # No silent conversion to derived units such as Ah.
    assert integral_unit("Ah") == "Ah·s"


def test_store_reads_full_resolution_regardless_of_decimation() -> None:
    # 20 001 samples of v(t) = t on [0, 20]: a decimated plot series is lossy,
    # the integral is exact and label-order invariant.
    store = TraceStore()
    store.ingest_samples([
        DecodedSignalSample(i / 1000.0, "1", 0x100, "M", "Sig", i / 1000.0, "A")
        for i in range(20_001)
    ])
    series = store.signal_series("M", "Sig", max_points=100)
    assert series["downsampled"]
    forward = store.signal_integral("M", "Sig", 2.0005, 12.0005)
    backward = store.signal_integral("M", "Sig", 12.0005, 2.0005)
    expected = (12.0005**2 - 2.0005**2) / 2
    assert forward["integral"] == pytest.approx(expected, rel=1e-12)
    assert backward["integral"] == forward["integral"]


def _import_sample(client: TestClient) -> dict:
    r = client.post(
        "/api/import",
        json={"trace_path": str(FIX / "sample.asc"), "dbc_paths": [str(FIX / "sample.dbc")]},
    )
    assert r.status_code == 200
    return r.json()


def _full_series(client: TestClient) -> tuple[list[float], list[float]]:
    r = client.get("/api/series", params={
        "message": "EngineData", "signal": "EngineSpeed", "max_points": 50_000,
    })
    body = r.json()
    assert not body["downsampled"]
    return body["t"], body["v"]


def test_endpoint_matches_engine_over_full_resolution(client: TestClient) -> None:
    _import_sample(client)
    t, v = _full_series(client)
    assert len(t) >= 3
    a, b = (t[0] + t[1]) / 2, (t[-2] + t[-1]) / 2
    expected = integrate(list(zip(t, v, strict=True)), a, b, "rpm")
    r = client.get("/api/signal-integral", params={
        "message": "EngineData", "signal": "EngineSpeed", "a": b, "b": a,
    })
    assert r.status_code == 200
    body = r.json()
    assert body["available"] and body["unit"] == "rpm·s"
    assert body["integral"] == pytest.approx(expected["integral"], rel=1e-12)
    assert set(body) >= {"start_s", "end_s", "method", "integral", "unit", "reason"}
    assert "t" not in body and "v" not in body  # no trace payload


def test_endpoint_widens_a_narrow_cached_window_to_bracketing_samples(
    client: TestClient,
) -> None:
    _import_sample(client)
    t, v = _full_series(client)
    a, b = (t[0] + t[1]) / 2, (t[1] + t[2]) / 2
    # Re-import so the series cache only knows a zoomed window strictly inside
    # the neighbours; the integral must still interpolate both boundaries.
    _import_sample(client)
    client.get("/api/series", params={
        "message": "EngineData", "signal": "EngineSpeed",
        "start": a, "end": b, "max_points": 2,
    })
    r = client.get("/api/signal-integral", params={
        "message": "EngineData", "signal": "EngineSpeed", "a": a, "b": b,
    })
    body = r.json()
    expected = integrate(list(zip(t, v, strict=True)), a, b, "rpm")
    assert body["available"], body
    assert body["integral"] == pytest.approx(expected["integral"], rel=1e-12)


def test_endpoint_reports_unavailable_outside_coverage(client: TestClient) -> None:
    _import_sample(client)
    t, _ = _full_series(client)
    r = client.get("/api/signal-integral", params={
        "message": "EngineData", "signal": "EngineSpeed", "a": t[0] - 5, "b": t[0],
    })
    assert r.status_code == 200
    assert r.json()["reason"] == "no_coverage"


def test_endpoint_validates_input(client: TestClient) -> None:
    _import_sample(client)
    bad = client.get("/api/signal-integral", params={
        "message": "EngineData", "signal": "EngineSpeed", "a": "nan", "b": 1,
    })
    assert bad.status_code in (400, 422)
    unknown = client.get("/api/signal-integral", params={
        "message": "EngineData", "signal": "Nope", "a": 0, "b": 1,
    })
    assert unknown.status_code == 404
