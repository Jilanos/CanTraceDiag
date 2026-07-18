import threading
import time
from pathlib import Path

import pytest
from starlette.testclient import TestClient

import cantracediag.api as api_module
from cantracediag.decode import Decoder
from cantracediag.pipeline import import_trace

FIX = Path(__file__).parent / "fixtures"


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


def test_series_is_decoded_on_demand_and_reuses_cache(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0
    original = Decoder.decode_signal

    def counted_decode(self, frame, message_name, signal_name):
        nonlocal calls
        calls += 1
        return original(self, frame, message_name, signal_name)

    monkeypatch.setattr(Decoder, "decode_signal", counted_decode)
    assert _import(client).status_code == 200

    params = {"message": "EngineData", "signal": "EngineSpeed"}
    first = client.get("/api/series", params=params)
    assert first.status_code == 200
    first_calls = calls
    assert first_calls > 0

    second = client.get("/api/series", params=params)
    assert second.status_code == 200
    assert calls == first_calls
    assert second.json()["v"] == first.json()["v"]


def test_lazy_series_matches_eager_decode_values(client: TestClient) -> None:
    assert _import(client).status_code == 200
    params = {
        "message": "EngineData",
        "signal": "EngineSpeed",
        "start": 0.010,
        "end": 0.020,
    }

    lazy = client.get("/api/series", params=params).json()
    eager_store, _ = import_trace(FIX / "sample.asc", [FIX / "sample.dbc"], decode_samples=True)
    try:
        eager = eager_store.signal_series(
            "EngineData", "EngineSpeed", start_s=0.010, end_s=0.020
        )
    finally:
        eager_store.close()

    assert lazy["t"] == eager["t"]
    assert lazy["v"] == eager["v"]


def test_query_without_trace_returns_409(client: TestClient) -> None:
    assert client.get("/api/series", params={"message": "X", "signal": "Y"}).status_code == 409


def test_missing_trace_file_returns_404(client: TestClient) -> None:
    r = client.post("/api/import", json={"trace_path": "/nope/missing.asc", "dbc_paths": []})
    assert r.status_code == 404


def test_index_page_served(client: TestClient) -> None:
    r = client.get("/")
    assert r.status_code == 200
    assert "CanTraceDiag" in r.text


def test_favicon_served(client: TestClient) -> None:
    r = client.get("/favicon.ico")
    assert r.status_code == 200
    assert r.headers["content-type"] == "image/vnd.microsoft.icon"
    assert r.content.startswith(b"\x00\x00\x01\x00")


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


def test_failed_import_keeps_previous_session(client: TestClient, tmp_path: Path) -> None:
    assert _import(client).status_code == 200
    before = client.get("/api/status").json()
    assert before["loaded"] is True

    bad = tmp_path / "bad.dbc"
    bad.write_text("not a dbc")
    r = client.post(
        "/api/import",
        json={"trace_path": str(FIX / "sample.asc"), "dbc_paths": [str(bad)]},
    )

    assert r.status_code == 400
    after = client.get("/api/status").json()
    assert after["loaded"] is True
    assert after["summary"]["frames"] == before["summary"]["frames"]


def test_import_job_is_responsive_during_upload_import(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    real_import = api_module.import_trace
    indexing_started = threading.Event()
    release_import = threading.Event()

    def slow_import(*args, **kwargs):
        on_progress = kwargs.get("on_progress")
        if on_progress is not None:
            on_progress(0.42)
        indexing_started.set()
        assert release_import.wait(2.0)
        return real_import(*args, **kwargs)

    monkeypatch.setattr(api_module, "import_trace", slow_import)

    response: dict[str, object] = {}

    def run_import() -> None:
        response["result"] = client.post(
            "/api/import-files",
            files=[
                (
                    "trace",
                    ("sample.asc", (FIX / "sample.asc").read_bytes(), "application/octet-stream"),
                ),
                (
                    "dbcs",
                    ("sample.dbc", (FIX / "sample.dbc").read_bytes(), "application/octet-stream"),
                ),
            ],
        )

    worker = threading.Thread(target=run_import)
    worker.start()
    assert indexing_started.wait(2.0)

    start = time.perf_counter()
    job = client.get("/api/import-job").json()
    elapsed = time.perf_counter() - start
    release_import.set()
    worker.join(timeout=2.0)

    assert elapsed < 0.2
    assert job["phase"] == "indexing"
    assert job["progress"] > 0.4
    result = response["result"]
    assert result.status_code == 200
