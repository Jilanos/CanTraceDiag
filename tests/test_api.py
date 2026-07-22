import os
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
    assert trace["start_index"] == 0
    assert trace["prev_cursor"] is None


def test_trace_endpoint_first_load_and_cursor_pagination(client: TestClient) -> None:
    assert _import(client).status_code == 200
    first = client.get("/api/trace", params={"limit": 3}).json()
    assert first["start_index"] == 0
    assert len(first["rows"]) == 3
    assert first["prev_cursor"] is None
    assert first["next_cursor"]

    second = client.get("/api/trace", params={"limit": 3, "cursor": first["next_cursor"]}).json()
    assert second["start_index"] == 3
    assert second["prev_cursor"]
    assert len(second["rows"]) == 3


def test_trace_endpoint_rejects_invalid_cursor(client: TestClient) -> None:
    assert _import(client).status_code == 200
    r = client.get("/api/trace", params={"cursor": "not-a-cursor"})
    assert r.status_code == 400
    assert "Invalid trace cursor" in r.json()["detail"]


def test_cursor_batch_endpoint(client: TestClient) -> None:
    assert _import(client).status_code == 200
    r = client.post(
        "/api/cursors",
        json={
            "a": 0.012,
            "b": 0.022,
            "signals": [{"message": "EngineData", "signal": "EngineSpeed"}],
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["a"]["EngineData.EngineSpeed"]["timestamp_s"] == 0.010
    assert body["b"]["EngineData.EngineSpeed"]["timestamp_s"] == 0.020


def test_testclient_host_is_allowed_and_host_guard_still_rejects() -> None:
    client = TestClient(api_module.create_app())
    assert client.get("/api/status").status_code == 200
    hostile = client.get("/api/status", headers={"host": "evil.example"})
    assert hostile.status_code == 403
    assert hostile.json()["detail"] == "Host not allowed."


def test_origin_guard_rejects_cross_site_origin(client: TestClient) -> None:
    r = client.get("/api/status", headers={"origin": "https://evil.example"})
    assert r.status_code == 403
    assert r.json()["detail"] == "Origin not allowed."


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


def test_index_versions_bundled_assets_and_forbids_shell_cache(client: TestClient) -> None:
    """The shell must cache-bust every bundled script/style and never be stored.

    Regression guard for the stale-asset mismatch: a fresh index.html loading a
    cached (stale) main.js threw during bootstrap and killed panel resize,
    collapse and the view controls. Versioned URLs + a non-cacheable shell make
    that pairing impossible.
    """
    import re as _re

    r = client.get("/")
    assert r.status_code == 200

    # The shell itself must not be reused from cache (it embeds the token and
    # the asset version), so the browser always re-fetches matching assets.
    assert "no-store" in r.headers.get("cache-control", "").lower()

    # Every same-origin JS/CSS reference carries a ?v=<token> version.
    refs = _re.findall(r'(?:href|src)="(/static/[^"]+\.(?:js|css))(\?v=[0-9a-f]+)?"', r.text)
    assert refs, "expected bundled asset references in the shell"
    assert refs == [(path, ver) for path, ver in refs if ver], (
        "every bundled JS/CSS reference must be versioned; unversioned: "
        f"{[p for p, v in refs if not v]}"
    )
    # main.js specifically (the file whose stale copy caused the regression).
    assert any(path.endswith("/js/main.js") and ver for path, ver in refs)


def test_asset_version_rotates_when_a_bundled_file_changes(tmp_path, monkeypatch) -> None:
    """AC1: the version token must change when an asset's content changes."""
    web = tmp_path / "web"
    (web / "js").mkdir(parents=True)
    (web / "styles.css").write_text("a{}", encoding="utf-8")
    (web / "js" / "main.js").write_text("console.log(1);", encoding="utf-8")
    (web / "index.html").write_text("<html></html>", encoding="utf-8")
    monkeypatch.setattr(api_module, "_WEB_DIR", web)

    before = api_module._asset_version()
    # Rewrite a file with different content and a newer mtime.
    js = web / "js" / "main.js"
    js.write_text("console.log(2);console.log(3);", encoding="utf-8")
    os.utime(js, (js.stat().st_atime + 5, js.stat().st_mtime + 5))
    after = api_module._asset_version()

    assert before != after
    assert len(after) == 12 and all(c in "0123456789abcdef" for c in after)


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
