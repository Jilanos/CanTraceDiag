from pathlib import Path

import pytest
from starlette.testclient import TestClient

from cantracediag.api import create_app

FIX = Path(__file__).parent / "fixtures"


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


def _import(client: TestClient):
    return client.post(
        "/api/import",
        json={"trace_path": str(FIX / "sample.asc"), "dbc_paths": [str(FIX / "sample.dbc")]},
    )


def test_status_before_import(client: TestClient) -> None:
    assert client.get("/api/status").json() == {"loaded": False}


def test_import_and_query_flow(client: TestClient) -> None:
    r = _import(client)
    assert r.status_code == 200
    assert r.json()["summary"]["frames"] == 6

    signals = client.get("/api/signals").json()["signals"]
    assert any(s["signal_name"] == "EngineSpeed" for s in signals)

    series_p = {"message": "EngineData", "signal": "EngineSpeed"}
    series = client.get("/api/series", params=series_p).json()
    assert len(series["t"]) > 0

    cursor = client.get("/api/cursor", params={**series_p, "at": 0.012}).json()
    assert cursor["timestamp_s"] == 0.010

    trace = client.get("/api/trace", params={"limit": 100}).json()
    assert trace["total"] == 8


def test_query_without_trace_returns_409(client: TestClient) -> None:
    assert client.get("/api/series", params={"message": "X", "signal": "Y"}).status_code == 409


def test_missing_trace_file_returns_404(client: TestClient) -> None:
    r = client.post("/api/import", json={"trace_path": "/nope/missing.asc", "dbc_paths": []})
    assert r.status_code == 404


def test_index_page_served(client: TestClient) -> None:
    r = client.get("/")
    assert r.status_code == 200
    assert "CanTraceDiag" in r.text
