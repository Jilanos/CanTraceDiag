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


def test_import_files_upload_flow(client: TestClient) -> None:
    asc = (FIX / "sample.asc").read_bytes()
    dbc = (FIX / "sample.dbc").read_bytes()
    r = client.post(
        "/api/import-files",
        files=[
            ("trace", ("sample.asc", asc, "application/octet-stream")),
            ("dbcs", ("sample.dbc", dbc, "application/octet-stream")),
            # A non-DBC file (e.g. picked from a folder) must be ignored.
            ("dbcs", ("notes.txt", b"ignore me", "text/plain")),
        ],
    )
    assert r.status_code == 200
    body = r.json()
    assert body["summary"]["frames"] == 6
    assert body["dbc_paths"] == ["sample.dbc"]
    # The query surface works after an upload-based import.
    assert client.get("/api/trace", params={"limit": 100}).json()["total"] == 8


def test_import_files_rejects_non_asc(client: TestClient) -> None:
    r = client.post(
        "/api/import-files",
        files=[("trace", ("trace.blf", b"\x00", "application/octet-stream"))],
    )
    assert r.status_code == 400


def test_import_job_reports_completed_import(client: TestClient) -> None:
    r = _import(client)
    assert r.status_code == 200
    job = client.get("/api/import-job").json()
    assert job["phase"] == "complete"
    assert job["progress"] == 1.0
    assert job["cancellable"] is False
    assert client.post("/api/import-cancel").json()["cancelled"] is False


def test_import_files_rejects_duplicate_dbc_basename(client: TestClient) -> None:
    asc = (FIX / "sample.asc").read_bytes()
    dbc = (FIX / "sample.dbc").read_bytes()
    r = client.post(
        "/api/import-files",
        files=[
            ("trace", ("sample.asc", asc, "application/octet-stream")),
            ("dbcs", ("same.dbc", dbc, "application/octet-stream")),
            ("dbcs", ("same.dbc", dbc, "application/octet-stream")),
        ],
    )
    assert r.status_code == 400
    assert "Duplicate DBC basename" in r.json()["detail"]


def test_import_rejects_invalid_dbc(client: TestClient, tmp_path: Path) -> None:
    bad = tmp_path / "bad.dbc"
    bad.write_text("not a dbc")
    r = client.post(
        "/api/import",
        json={"trace_path": str(FIX / "sample.asc"), "dbc_paths": [str(bad)]},
    )
    assert r.status_code == 400
    assert "Invalid DBC" in r.json()["detail"]
