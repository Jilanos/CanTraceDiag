"""Persistent workspace: DBC library, session restore, LRU, purge (req_006)."""

from __future__ import annotations

import json
from pathlib import Path

from starlette.testclient import TestClient

from cantracediag.api import create_app
from cantracediag.workspace import Workspace

FIX = Path(__file__).parent / "fixtures"


def _client(app) -> TestClient:
    client = TestClient(app)
    client.headers.update({"X-CTD-Token": app.state.ctd_security.token})
    return client


def _persistent(tmp_path: Path, **kw) -> Workspace:
    return Workspace(tmp_path / "ws", ephemeral=False, **kw)


# -- DBC library -------------------------------------------------------------
def test_dbc_library_dedup_and_survives_reopen(tmp_path: Path) -> None:
    ws = _persistent(tmp_path)
    a = ws.store_dbc(FIX / "sample.dbc", "sample.dbc")
    b = ws.store_dbc(FIX / "sample.dbc", "sample.dbc")  # identical content
    assert a.digest == b.digest
    assert len(ws.library()) == 1  # deduplicated by content hash (AC4)

    # A fresh Workspace on the same root still sees it (survives "restart").
    reopened = Workspace(ws.root, ephemeral=False)
    lib = reopened.library()
    assert len(lib) == 1
    assert lib[0].name == "sample.dbc"
    assert reopened.library_path(a.digest) is not None


def test_lru_eviction(tmp_path: Path) -> None:
    ws = _persistent(tmp_path, dbc_cap=2)
    for i in range(3):
        # distinct content -> distinct digests
        f = tmp_path / f"d{i}.dbc"
        f.write_text((FIX / "sample.dbc").read_text() + f"\n// {i}\n")
        ws.store_dbc(f, f.name)
    lib = ws.library()
    assert len(lib) == 2  # oldest evicted (AC8)
    names = {e.name for e in lib}
    assert names == {"d1.dbc", "d2.dbc"}


def test_purge_clears_library_and_manifest(tmp_path: Path) -> None:
    ws = _persistent(tmp_path)
    ws.store_dbc(FIX / "sample.dbc", "sample.dbc")
    ws.manifest_path.write_text('{"schema_version": 1}')
    ws.purge()
    assert ws.library() == []
    assert not ws.manifest_path.exists()


def test_ephemeral_persists_nothing(tmp_path: Path) -> None:
    ws = Workspace(tmp_path / "eph", ephemeral=True)
    ws.store_dbc(FIX / "sample.dbc", "sample.dbc")
    assert ws.library() == []
    _, holder = ws.new_analysis_holder()
    ws.commit_analysis(holder, trace_display="t", asc_base="hex", dbcs=[], resolution={})
    assert ws.load_manifest() is None  # AC10: nothing survives


# -- session restore across a simulated restart ------------------------------
def test_session_restore_after_restart(tmp_path: Path) -> None:
    ws1 = _persistent(tmp_path)
    app1 = create_app(ws1)
    c1 = _client(app1)
    r = c1.post(
        "/api/import",
        json={"trace_path": str(FIX / "sample.asc"), "dbc_paths": [str(FIX / "sample.dbc")]},
    )
    assert r.status_code == 200
    frames = r.json()["summary"]["frames"]
    assert c1.get("/api/status").json()["loaded"] is True

    # Simulate a server restart: close the live DuckDB connection (leaving the
    # persisted files intact), then build a brand-new app on the same workspace.
    app1.state.ctd_session.store.close()

    app2 = create_app(Workspace(ws1.root, ephemeral=False))
    c2 = _client(app2)
    status = c2.get("/api/status").json()
    assert status["loaded"] is True                       # AC6: restored
    assert status["summary"]["frames"] == frames          # no re-import/re-parse
    # And a decoded query works against the restored store.
    sigs = c2.get("/api/signals").json()["signals"]
    assert sigs, "signals should come from the restored catalog"


def test_corrupt_manifest_starts_empty(tmp_path: Path) -> None:
    ws = _persistent(tmp_path)
    ws.manifest_path.write_text("{ this is not valid json ")
    app = create_app(Workspace(ws.root, ephemeral=False))  # must not crash (AC7)
    c = _client(app)
    assert c.get("/api/status").json() == {"loaded": False}


def test_missing_library_dbc_starts_empty(tmp_path: Path) -> None:
    ws = _persistent(tmp_path)
    # A manifest referencing a library DBC that is not on disk is incoherent.
    ws.manifest_path.write_text(json.dumps({
        "schema_version": 1, "holder": "deadbeef", "duckdb": "analysis.duckdb",
        "trace_display": "x.asc", "asc_base": "hex",
        "dbcs": [{"digest": "missing", "name": "gone.dbc"}], "resolution": {},
    }))
    app = create_app(Workspace(ws.root, ephemeral=False))
    c = _client(app)
    assert c.get("/api/status").json() == {"loaded": False}


# -- import reusing a library DBC without re-upload (AC5) ---------------------
def test_import_files_reuses_library_dbc(tmp_path: Path) -> None:
    ws = _persistent(tmp_path)
    app = create_app(ws)
    c = _client(app)

    asc = (FIX / "sample.asc").read_bytes()
    dbc = (FIX / "sample.dbc").read_bytes()
    octet = "application/octet-stream"

    # First import via upload populates the library.
    r = c.post(
        "/api/import-files",
        files=[
            ("trace", ("sample.asc", asc, octet)),
            ("dbcs", ("sample.dbc", dbc, octet)),
        ],
    )
    assert r.status_code == 200
    lib = c.get("/api/dbc-library").json()["dbcs"]
    assert len(lib) == 1
    digest = lib[0]["digest"]

    # Second import: trace upload only, DBC pulled from the library by digest.
    r2 = c.post(
        "/api/import-files",
        files=[("trace", ("sample.asc", asc, octet))],
        data={"library": [digest]},
    )
    assert r2.status_code == 200
    assert r2.json()["summary"]["decoded_frames"] > 0  # decoded via the library DBC
