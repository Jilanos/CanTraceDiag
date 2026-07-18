"""Hostile tests for local and LAN API hardening (task_019, AC10-AC11).

Each defence is checked from the attacker's side: a disallowed Host or Origin,
a missing/invalid token, an oversized upload, LAN-mode token enforcement, and
server-path import being disabled in LAN. Error messages must not leak local
filesystem paths.
"""

from __future__ import annotations

from pathlib import Path

from conftest import make_client
from starlette.testclient import TestClient

from cantracediag.api import create_app
from cantracediag.security import LOOPBACK_HOSTS, SecurityConfig

FIX = Path(__file__).parent / "fixtures"


def _config(**kw) -> SecurityConfig:
    base = dict(
        lan=False,
        token="secret-token",
        allowed_hosts=frozenset(LOOPBACK_HOSTS),
        max_upload_bytes=512 * 1024 * 1024,
        allow_server_import=True,
    )
    base.update(kw)
    return SecurityConfig(**base)


def _bare_client(app, base_url="http://localhost") -> TestClient:
    """A client with no session token, for asserting rejections."""
    return TestClient(app, base_url=base_url)


def _import_body() -> dict:
    return {"trace_path": str(FIX / "sample.asc"), "dbc_paths": [str(FIX / "sample.dbc")]}


# -- Host / Origin (AC10) -------------------------------------------------


def test_disallowed_host_is_rejected() -> None:
    app = create_app(security=_config())
    client = TestClient(app, base_url="http://evil.example.com",
                        headers={"X-CTD-Token": "secret-token"})
    r = client.get("/api/status")
    assert r.status_code == 403
    assert r.json()["detail"] == "Host not allowed."


def test_cross_origin_request_is_rejected() -> None:
    app = create_app(security=_config())
    client = make_client(app)
    r = client.get("/api/status", headers={"Origin": "http://evil.example.com"})
    assert r.status_code == 403
    assert r.json()["detail"] == "Origin not allowed."


def test_same_origin_request_is_allowed() -> None:
    app = create_app(security=_config())
    client = make_client(app)
    r = client.get("/api/status", headers={"Origin": "http://localhost"})
    assert r.status_code == 200


# -- session token (AC10) -------------------------------------------------


def test_mutation_without_token_is_rejected_locally() -> None:
    app = create_app(security=_config())
    r = _bare_client(app).post("/api/import", json=_import_body())
    assert r.status_code == 401
    assert r.json()["detail"] == "Missing or invalid session token."


def test_mutation_with_wrong_token_is_rejected() -> None:
    app = create_app(security=_config())
    client = TestClient(app, base_url="http://localhost",
                        headers={"X-CTD-Token": "wrong"})
    assert client.post("/api/import", json=_import_body()).status_code == 401


def test_read_endpoints_need_no_token_locally() -> None:
    app = create_app(security=_config())
    assert _bare_client(app).get("/api/status").status_code == 200


def test_mutation_with_token_succeeds() -> None:
    app = create_app(security=_config())
    assert make_client(app).post("/api/import", json=_import_body()).status_code == 200


# -- LAN mode (AC10, AC11) ------------------------------------------------


def test_lan_mode_requires_token_on_reads() -> None:
    app = create_app(security=_config(lan=True, allow_server_import=False))
    # No token: even a read is rejected in LAN mode.
    assert _bare_client(app).get("/api/status").status_code == 401
    # With the token, the read succeeds.
    assert make_client(app).get("/api/status").status_code == 200


def test_lan_mode_disables_server_path_import() -> None:
    app = create_app(security=_config(lan=True, allow_server_import=False))
    r = make_client(app).post("/api/import", json=_import_body())
    assert r.status_code == 403
    assert r.json()["detail"] == "Server-side path import is disabled."


def test_lan_mode_index_requires_token() -> None:
    app = create_app(security=_config(lan=True, allow_server_import=False))
    assert _bare_client(app).get("/").status_code == 401
    assert make_client(app).get("/").status_code == 200


# -- upload cap (AC10) ----------------------------------------------------


def test_upload_over_limit_is_rejected() -> None:
    app = create_app(security=_config(max_upload_bytes=64))
    big = b"0.0 1 100 Rx d 8 " + b"00 " * 4000
    r = make_client(app).post(
        "/api/import-files",
        files=[("trace", ("big.asc", big, "application/octet-stream"))],
    )
    assert r.status_code == 413
    assert "size limit" in r.json()["detail"]


# -- no path leakage (AC10) -----------------------------------------------


def test_missing_file_error_does_not_leak_paths() -> None:
    app = create_app(security=_config())
    r = make_client(app).post(
        "/api/import",
        json={"trace_path": "/home/secret/vehicle/trace.asc", "dbc_paths": []},
    )
    assert r.status_code == 404
    detail = r.json()["detail"]
    assert "/home/secret" not in detail
    assert "trace.asc" not in detail


# -- token delivery to the UI shell ---------------------------------------


def test_index_embeds_session_token_locally() -> None:
    app = create_app(security=_config())
    html = make_client(app).get("/").text
    assert '<meta name="ctd-token" content="secret-token" />' in html
