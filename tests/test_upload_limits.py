"""Streaming upload budgets and staging rollback (req_034 AC1, AC3, AC10).

The byte budgets are exercised at scaled-down sizes so the suite stays fast; the
boundary semantics (inclusive trace cap, independent DBC and envelope budgets,
whole-request cap) are identical at the shipped 1 GiB / 64 MiB / 8 MiB defaults,
which are pinned separately below. The full-size boundary runs in the Windows
qualification script.
"""

from __future__ import annotations

import asyncio
import uuid
from pathlib import Path

import pytest
from conftest import make_client
from starlette.requests import Request

import cantracediag.api as api_module
from cantracediag.api import TRACE_SUFFIXES, create_app
from cantracediag.security import (
    LOOPBACK_HOSTS,
    MIB,
    SecurityConfig,
    UploadLimits,
)
from cantracediag.upload import UploadCancelled, UploadRejected, format_bytes, stage_multipart
from cantracediag.workspace import Workspace

FIX = Path(__file__).parent / "fixtures"
SAMPLE = (FIX / "sample.asc").read_bytes()
SAMPLE_DBC = (FIX / "sample.dbc").read_bytes()


def _config(limits: UploadLimits) -> SecurityConfig:
    return SecurityConfig(
        lan=False,
        token="secret-token",
        allowed_hosts=frozenset(LOOPBACK_HOSTS),
        upload_limits=limits,
        allow_server_import=True,
    )


def _multipart(parts: list[tuple[str, str | None, bytes]]) -> tuple[bytes, str]:
    """Encode ``(field, filename|None, payload)`` parts; returns body and content type."""
    boundary = uuid.uuid4().hex
    out = bytearray()
    for name, filename, payload in parts:
        out += f"--{boundary}\r\n".encode()
        disposition = f'form-data; name="{name}"'
        if filename is not None:
            disposition += f'; filename="{filename}"'
        out += f"Content-Disposition: {disposition}\r\n".encode()
        if filename is not None:
            out += b"Content-Type: application/octet-stream\r\n"
        out += b"\r\n" + payload + b"\r\n"
    out += f"--{boundary}--\r\n".encode()
    return bytes(out), f"multipart/form-data; boundary={boundary}"


def _padded_trace(size: int) -> bytes:
    """A valid ASC of exactly ``size`` bytes (trailing comment padding)."""
    assert size >= len(SAMPLE) + 4
    pad = size - len(SAMPLE) - 3
    return SAMPLE + b"//" + b" " * pad + b"\n"


def _post(app, body: bytes, content_type: str, headers: dict | None = None):
    client = make_client(app)
    hdrs = {"content-type": content_type, **(headers or {})}
    return client.post("/api/import-files", content=body, headers=hdrs)


# -- shipped defaults --------------------------------------------------------


def test_default_limits_are_inclusive_1_gib_plus_independent_budgets(monkeypatch) -> None:
    for name in ("CANTRACEDIAG_MAX_TRACE_MB", "CANTRACEDIAG_MAX_DBC_MB",
                 "CANTRACEDIAG_MAX_ENVELOPE_MB", "CANTRACEDIAG_MAX_UPLOAD_MB"):
        monkeypatch.delenv(name, raising=False)
    limits = UploadLimits.from_env(lan=False)
    assert limits.trace == 1_073_741_824
    assert limits.dbc == 64 * MIB
    assert limits.envelope == 8 * MIB
    assert limits.max_request == 1_073_741_824 + 72 * MIB
    assert format_bytes(limits.trace) == "1 GiB (1,073,741,824 bytes)"


def test_lan_keeps_legacy_aggregate_cap_unless_overridden(monkeypatch) -> None:
    for name in ("CANTRACEDIAG_MAX_TRACE_MB", "CANTRACEDIAG_MAX_DBC_MB",
                 "CANTRACEDIAG_MAX_ENVELOPE_MB", "CANTRACEDIAG_MAX_UPLOAD_MB"):
        monkeypatch.delenv(name, raising=False)
    lan = UploadLimits.from_env(lan=True)
    assert lan.max_request == 512 * MIB
    assert lan.trace == 512 * MIB
    monkeypatch.setenv("CANTRACEDIAG_MAX_TRACE_MB", "1024")
    assert UploadLimits.from_env(lan=True).trace == 1024 * MIB


def test_explicit_aggregate_override_caps_trace_and_request(monkeypatch) -> None:
    monkeypatch.delenv("CANTRACEDIAG_MAX_TRACE_MB", raising=False)
    monkeypatch.setenv("CANTRACEDIAG_MAX_UPLOAD_MB", "256")
    limits = UploadLimits.from_env(lan=False)
    assert limits.max_request == 256 * MIB
    assert limits.trace == 256 * MIB
    monkeypatch.setenv("CANTRACEDIAG_MAX_UPLOAD_MB", "not-a-number")
    assert UploadLimits.from_env(lan=False).trace == 1024 * MIB


# -- trace boundary: cap - 1, exact, cap + 1 ----------------------------------

CAP = 4096


@pytest.mark.parametrize(("size", "status"), [(CAP - 1, 200), (CAP, 200), (CAP + 1, 413)])
def test_trace_cap_is_inclusive(size: int, status: int) -> None:
    app = create_app(security=_config(UploadLimits(trace=CAP, dbc=CAP, envelope=1024)))
    body, ctype = _multipart([("trace", "t.asc", _padded_trace(size))])
    r = _post(app, body, ctype)
    assert r.status_code == status, r.text
    if status == 200:
        assert r.json()["summary"]["frames"] > 0
    else:
        assert "Trace file exceeds the 4 KiB (4,096 bytes) limit" in r.json()["detail"]


def test_trace_cap_independent_of_dbc_budget() -> None:
    """A full-cap trace plus DBCs is accepted: DBCs never eat the trace budget."""
    limits = UploadLimits(trace=CAP, dbc=len(SAMPLE_DBC) * 2 + 16, envelope=1024)
    app = create_app(security=_config(limits))
    body, ctype = _multipart([
        ("trace", "t.asc", _padded_trace(CAP)),
        ("dbcs", "a.dbc", SAMPLE_DBC),
        ("dbcs", "b.dbc", SAMPLE_DBC.replace(b"BU_:", b"BU_: X", 1)),
    ])
    r = _post(app, body, ctype)
    assert r.status_code == 200, r.text


def test_dbc_budget_is_aggregate_and_separate() -> None:
    limits = UploadLimits(trace=CAP * 4, dbc=len(SAMPLE_DBC) + 10, envelope=1024)
    app = create_app(security=_config(limits))
    body, ctype = _multipart([
        ("trace", "t.asc", SAMPLE),
        ("dbcs", "a.dbc", SAMPLE_DBC),
        ("dbcs", "b.dbc", SAMPLE_DBC),
    ])
    r = _post(app, body, ctype)
    assert r.status_code == 413
    assert "Uploaded DBC total exceeds" in r.json()["detail"]


def test_ignored_folder_entries_count_against_dbc_budget() -> None:
    limits = UploadLimits(trace=CAP * 4, dbc=100, envelope=1024)
    app = create_app(security=_config(limits))
    body, ctype = _multipart([("trace", "t.asc", SAMPLE), ("dbcs", "readme.txt", b"x" * 200)])
    assert _post(app, body, ctype).status_code == 413


def test_envelope_budget_bounds_form_fields() -> None:
    limits = UploadLimits(trace=CAP * 4, dbc=CAP, envelope=600)
    app = create_app(security=_config(limits))
    fields = [("library", None, b"f" * 64) for _ in range(20)]
    body, ctype = _multipart([("trace", "t.asc", SAMPLE), *fields])
    r = _post(app, body, ctype)
    assert r.status_code == 413
    assert "envelope" in r.json()["detail"]


def test_declared_content_length_over_request_cap_rejected_early() -> None:
    limits = UploadLimits(trace=CAP, dbc=CAP, envelope=1024)
    app = create_app(security=_config(limits))
    body, ctype = _multipart([("trace", "t.asc", SAMPLE)])
    r = _post(app, body, ctype, {"content-length": str(limits.max_request + 1)})
    assert r.status_code == 413
    assert "Upload exceeds" in r.json()["detail"]


def test_misleading_small_content_length_cannot_bypass_trace_cap() -> None:
    app = create_app(security=_config(UploadLimits(trace=CAP, dbc=CAP, envelope=1024)))
    body, ctype = _multipart([("trace", "t.asc", _padded_trace(CAP + 1))])
    r = _post(app, body, ctype, {"content-length": "100"})
    assert r.status_code == 413


def test_missing_content_length_still_enforced_while_streaming() -> None:
    app = create_app(security=_config(UploadLimits(trace=CAP, dbc=CAP, envelope=1024)))
    body, ctype = _multipart([("trace", "t.asc", _padded_trace(CAP + 1))])

    def chunks():
        for i in range(0, len(body), 512):
            yield body[i:i + 512]

    client = make_client(app)
    r = client.post("/api/import-files", content=chunks(), headers={"content-type": ctype})
    assert "content-length" not in {k.lower() for k in r.request.headers}
    assert r.status_code == 413


def test_wrong_suffix_and_missing_trace_rejected() -> None:
    app = create_app(security=_config(UploadLimits()))
    body, ctype = _multipart([("trace", "t.txt", SAMPLE)])
    assert _post(app, body, ctype).status_code == 400
    body, ctype = _multipart([("dbcs", "a.dbc", SAMPLE_DBC)])
    r = _post(app, body, ctype)
    assert r.status_code == 400
    assert "No trace file" in r.json()["detail"]
    r = _post(app, b"not multipart", "text/plain")
    assert r.status_code == 400


def test_duplicate_dbc_basename_rejected() -> None:
    app = create_app(security=_config(UploadLimits()))
    body, ctype = _multipart([
        ("trace", "t.asc", SAMPLE),
        ("dbcs", "a.dbc", SAMPLE_DBC),
        ("dbcs", "dir/a.dbc", SAMPLE_DBC),
    ])
    r = _post(app, body, ctype)
    assert r.status_code == 400
    assert "Duplicate DBC basename" in r.json()["detail"]


# -- rollback: rejected / cancelled uploads keep the previous analysis --------


def _staging_children(ws: Workspace) -> list[Path]:
    return list(ws.staging_dir.iterdir()) if ws.staging_dir.is_dir() else []


def test_rejected_upload_removes_staging_and_keeps_previous_analysis(tmp_path: Path) -> None:
    ws = Workspace(tmp_path / "ws")
    app = create_app(ws, security=_config(UploadLimits(trace=CAP, dbc=CAP, envelope=1024)))
    client = make_client(app)
    body, ctype = _multipart([("trace", "first.asc", SAMPLE)])
    first = client.post("/api/import-files", content=body, headers={"content-type": ctype})
    assert first.status_code == 200
    frames = first.json()["summary"]["frames"]

    body, ctype = _multipart([("trace", "second.asc", _padded_trace(CAP + 1))])
    r = client.post("/api/import-files", content=body, headers={"content-type": ctype})
    assert r.status_code == 413
    assert _staging_children(ws) == []
    status = client.get("/api/status").json()
    assert status["loaded"] is True
    assert status["trace_path"] == "first.asc"
    assert status["summary"]["frames"] == frames
    job = client.get("/api/import-job").json()
    assert job["phase"] == "failed" and "exceeds" in job["detail"]


def test_stale_staging_is_pruned_on_startup(tmp_path: Path) -> None:
    ws = Workspace(tmp_path / "ws")
    leftover = ws.new_staging_dir()
    (leftover / "trace").mkdir()
    (leftover / "trace" / "half.asc").write_bytes(b"x" * 10)
    create_app(ws, security=_config(UploadLimits()))
    assert _staging_children(ws) == []


def _request_from_chunks(body: bytes, ctype: str, chunk: int = 256) -> Request:
    pieces = [body[i:i + chunk] for i in range(0, len(body), chunk)]

    async def receive():
        if pieces:
            return {"type": "http.request", "body": pieces.pop(0), "more_body": bool(pieces)}
        return {"type": "http.disconnect"}

    scope = {
        "type": "http", "method": "POST", "path": "/api/import-files",
        "headers": [(b"content-type", ctype.encode())],
    }
    return Request(scope, receive)


def test_cancel_during_transfer_stops_streaming(tmp_path: Path) -> None:
    body, ctype = _multipart([("trace", "t.asc", _padded_trace(CAP))])
    calls = {"n": 0}

    def cancel_after_two_chunks() -> bool:
        calls["n"] += 1
        return calls["n"] > 2

    with pytest.raises(UploadCancelled):
        asyncio.run(stage_multipart(
            _request_from_chunks(body, ctype), tmp_path, UploadLimits(),
            trace_suffixes=TRACE_SUFFIXES, cancel_check=cancel_after_two_chunks,
        ))
    staged = tmp_path / "trace" / "t.asc"
    assert staged.stat().st_size < CAP  # stopped mid-transfer, caller removes it


def test_truncated_body_is_rejected(tmp_path: Path) -> None:
    body, ctype = _multipart([("trace", "t.asc", SAMPLE)])
    request = _request_from_chunks(body[: len(body) // 2], ctype)
    request.scope["headers"].append((b"content-length", str(len(body)).encode()))
    with pytest.raises(UploadRejected) as exc:
        asyncio.run(stage_multipart(
            request, tmp_path, UploadLimits(), trace_suffixes=TRACE_SUFFIXES,
        ))
    assert exc.value.status == 400


def test_insufficient_disk_space_is_actionable(monkeypatch, tmp_path: Path) -> None:
    class _Usage:
        free = 1024

    monkeypatch.setattr("cantracediag.upload.shutil.disk_usage", lambda _p: _Usage())
    app = create_app(security=_config(UploadLimits()))
    body, ctype = _multipart([("trace", "t.asc", SAMPLE)])
    r = _post(app, body, ctype)
    assert r.status_code == 507
    assert "free disk space" in r.json()["detail"]


def test_cancel_flag_before_indexing_aborts_without_replacing(monkeypatch, tmp_path) -> None:
    """A cancel that lands between upload and indexing never publishes."""
    ws = Workspace(tmp_path / "ws")
    app = create_app(ws, security=_config(UploadLimits()))
    client = make_client(app)
    body, ctype = _multipart([("trace", "first.asc", SAMPLE)])
    assert client.post("/api/import-files", content=body,
                       headers={"content-type": ctype}).status_code == 200

    real_stage = api_module.stage_multipart

    async def stage_then_cancel(*args, **kwargs):
        staged = await real_stage(*args, **kwargs)
        app.state.ctd_session.cancel_event.set()
        return staged

    monkeypatch.setattr(api_module, "stage_multipart", stage_then_cancel)
    body, ctype = _multipart([("trace", "second.asc", SAMPLE)])
    r = client.post("/api/import-files", content=body, headers={"content-type": ctype})
    assert r.status_code == 409
    assert client.get("/api/status").json()["trace_path"] == "first.asc"
    assert _staging_children(ws) == []
