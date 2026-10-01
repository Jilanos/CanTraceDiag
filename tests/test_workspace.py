"""Persistent workspace: DBC library, session restore, LRU, purge (req_006)."""

from __future__ import annotations

import json
from pathlib import Path

from conftest import make_client

from cantracediag.api import create_app
from cantracediag.workspace import Workspace

FIX = Path(__file__).parent / "fixtures"


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
    c1 = make_client(app1)
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
    c2 = make_client(app2)
    status = c2.get("/api/status").json()
    assert status["loaded"] is True                       # AC6: restored
    assert status["summary"]["frames"] == frames          # no re-import/re-parse
    # And a decoded query works against the restored store.
    sigs = c2.get("/api/signals").json()["signals"]
    assert sigs, "signals should come from the restored catalog"


def test_restored_analysis_ranks_databases_by_library_recency(tmp_path: Path) -> None:
    """The active DBC is the most recently used one of the restored analysis (AC2).

    A restore reads the manifest, which records the load order; the library is
    what knows recency, so a DBC used again since the import must rank first.
    """
    ws1 = _persistent(tmp_path)
    app1 = create_app(ws1)
    c1 = make_client(app1)
    r = c1.post(
        "/api/import",
        json={
            "trace_path": str(FIX / "sample.asc"),
            "dbc_paths": [str(FIX / "sample.dbc"), str(FIX / "sample_body.dbc")],
        },
    )
    assert r.status_code == 200
    assert c1.get("/api/signals").json()["active_database"] == "sample.dbc"
    app1.state.ctd_session.store.close()

    # Simulate the second DBC having been used again after this analysis.
    index = json.loads(ws1.index_path.read_text())
    for meta in index.values():
        meta["last_used"] = "2030-01-01T00:00:00Z" if meta["name"] == "sample_body.dbc" \
            else "2020-01-01T00:00:00Z"
    ws1.index_path.write_text(json.dumps(index))

    c2 = make_client(create_app(Workspace(ws1.root, ephemeral=False)))
    payload = c2.get("/api/signals").json()
    assert payload["databases"] == ["sample_body.dbc", "sample.dbc"]
    assert payload["active_database"] == "sample_body.dbc"


def test_corrupt_manifest_starts_empty(tmp_path: Path) -> None:
    ws = _persistent(tmp_path)
    ws.manifest_path.write_text("{ this is not valid json ")
    app = create_app(Workspace(ws.root, ephemeral=False))  # must not crash (AC7)
    c = make_client(app)
    assert c.get("/api/status").json()["loaded"] is False


def test_missing_library_dbc_starts_empty(tmp_path: Path) -> None:
    ws = _persistent(tmp_path)
    # A manifest referencing a library DBC that is not on disk is incoherent.
    ws.manifest_path.write_text(json.dumps({
        "schema_version": 1, "holder": "deadbeef", "duckdb": "analysis.duckdb",
        "trace_display": "x.asc", "asc_base": "hex",
        "dbcs": [{"digest": "missing", "name": "gone.dbc"}], "resolution": {},
    }))
    app = create_app(Workspace(ws.root, ephemeral=False))
    c = make_client(app)
    assert c.get("/api/status").json()["loaded"] is False


# -- import reusing a library DBC without re-upload (AC5) ---------------------
def test_import_files_reuses_library_dbc(tmp_path: Path) -> None:
    ws = _persistent(tmp_path)
    app = create_app(ws)
    c = make_client(app)

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


# -- remembered DBC selection by content identity (req_032 AC4/AC5) ----------
_OCTET = "application/octet-stream"


def _upload(c, dbcs: list[tuple[str, bytes]], library: list[str] | None = None):
    files = [("trace", ("sample.asc", (FIX / "sample.asc").read_bytes(), _OCTET))]
    files += [("dbcs", (name, data, _OCTET)) for name, data in dbcs]
    return c.post("/api/import-files", files=files, data={"library": library or []})


def _digest_of(c, name: str) -> str:
    return next(e["digest"] for e in c.get("/api/dbc-library").json()["dbcs"] if e["name"] == name)


def test_mixed_uploaded_and_reused_set_survives_restart(tmp_path: Path) -> None:
    ws = _persistent(tmp_path)
    app = create_app(ws)
    c = make_client(app)
    assert c.get("/api/dbc-library").json()["last_session_digests"] == []  # first use

    assert _upload(c, [("sample.dbc", (FIX / "sample.dbc").read_bytes())]).status_code == 200
    reused = _digest_of(c, "sample.dbc")
    r = _upload(c, [("sample_body.dbc", (FIX / "sample_body.dbc").read_bytes())], [reused])
    assert r.status_code == 200
    uploaded = _digest_of(c, "sample_body.dbc")
    assert c.get("/api/dbc-library").json()["last_session_digests"] == [uploaded, reused]

    app.state.ctd_session.store.close()
    c2 = make_client(create_app(Workspace(ws.root, ephemeral=False)))
    assert c2.get("/api/dbc-library").json()["last_session_digests"] == [uploaded, reused]
    # A trace-only load reusing the remembered set decodes without re-upload.
    r2 = _upload(c2, [], [uploaded, reused])
    assert r2.status_code == 200
    assert r2.json()["summary"]["decoded_frames"] > 0


def test_same_name_different_content_stays_distinct(tmp_path: Path) -> None:
    c = make_client(create_app(_persistent(tmp_path)))
    assert _upload(c, [("common.dbc", (FIX / "sample.dbc").read_bytes())]).status_code == 200
    first = c.get("/api/dbc-library").json()["last_session_digests"]
    assert _upload(c, [("common.dbc", (FIX / "sample_body.dbc").read_bytes())]).status_code == 200
    payload = c.get("/api/dbc-library").json()
    second = payload["last_session_digests"]
    assert len(first) == len(second) == 1 and first != second
    assert sorted(e["digest"] for e in payload["dbcs"]) == sorted(first + second)


def test_failed_and_unresolved_imports_keep_previous_history(tmp_path: Path) -> None:
    c = make_client(create_app(_persistent(tmp_path)))
    assert _upload(c, [("sample.dbc", (FIX / "sample.dbc").read_bytes())]).status_code == 200
    before = c.get("/api/dbc-library").json()["last_session_digests"]

    assert _upload(c, [("broken.dbc", b"this is not a dbc")]).status_code == 400
    assert c.get("/api/dbc-library").json()["last_session_digests"] == before

    conflict = _upload(
        c, [("sample_conflict.dbc", (FIX / "sample_conflict.dbc").read_bytes())], before,
    )
    assert conflict.json()["needs_resolution"] is True
    assert c.get("/api/dbc-library").json()["last_session_digests"] == before  # unresolved

    resolved = c.post("/api/resolve", json={"resolution": {"0x100": "sample.dbc"}})
    assert resolved.status_code == 200
    after = c.get("/api/dbc-library").json()["last_session_digests"]
    assert len(after) == 2 and before[0] in after


def test_malformed_history_and_purge_degrade_to_empty(tmp_path: Path) -> None:
    ws = _persistent(tmp_path)
    c = make_client(create_app(ws))
    assert _upload(c, [("sample.dbc", (FIX / "sample.dbc").read_bytes())]).status_code == 200
    manifest = json.loads(ws.manifest_path.read_text())
    manifest["dbcs"] = [{"name": "legacy.dbc"}, "garbage", {"digest": 7}]
    ws.manifest_path.write_text(json.dumps(manifest))
    assert ws.last_dbc_digests() == []
    assert c.get("/api/dbc-library").json()["last_session_digests"] == []

    assert _upload(c, [("sample.dbc", (FIX / "sample.dbc").read_bytes())]).status_code == 200
    assert c.get("/api/dbc-library").json()["last_session_digests"]
    assert c.post("/api/workspace-purge").status_code == 200
    payload = c.get("/api/dbc-library").json()
    assert payload["last_session_digests"] == [] and payload["dbcs"] == []
