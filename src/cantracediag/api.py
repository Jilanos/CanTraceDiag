"""Local query API and static UI host for CanTraceDiag.

The API holds a single in-process acquisition (one CAN bus, MVP scope) and
serves bounded queries so the browser never loads the whole trace (AC4-AC6,
AC8). It is local-first: it binds to localhost by default and reads trace/DBC
files from local disk paths supplied by the operator.
"""

from __future__ import annotations

import re
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from cantracediag.dbc import DbcCatalog
from cantracediag.pipeline import import_trace
from cantracediag.store import TraceStore

_WEB_DIR = Path(__file__).parent / "web"


class Session:
    """Holds the currently loaded acquisition."""

    def __init__(self) -> None:
        self.store: TraceStore | None = None
        self.catalog: DbcCatalog | None = None
        self.trace_path: str | None = None
        self.dbc_paths: list[str] = []
        self.ambiguous_ids: dict[int, list[str]] = {}
        self.asc_base: str | None = None

    def require_store(self) -> TraceStore:
        if self.store is None:
            raise HTTPException(status_code=409, detail="No trace loaded. POST /api/import first.")
        return self.store


class ImportRequest(BaseModel):
    trace_path: str
    dbc_paths: list[str] = []


def create_app() -> FastAPI:
    app = FastAPI(title="CanTraceDiag", version="0.1.0")
    session = Session()

    @app.post("/api/import")
    def api_import(req: ImportRequest) -> dict:
        trace = Path(normalize_local_path(req.trace_path)).expanduser()
        if not trace.is_file():
            raise HTTPException(404, f"Trace not found: {trace}")
        dbc_paths = [Path(normalize_local_path(d)).expanduser() for d in req.dbc_paths]
        for dbc in dbc_paths:
            if not dbc.is_file():
                raise HTTPException(404, f"DBC not found: {dbc}")

        if session.store is not None:
            session.store.close()

        catalog = DbcCatalog()
        for dbc in dbc_paths:
            catalog.load(dbc)

        store, result = import_trace(trace, dbc_paths)
        session.store = store
        session.catalog = catalog
        session.trace_path = str(trace)
        session.dbc_paths = [str(p) for p in dbc_paths]
        session.ambiguous_ids = result.ambiguous_ids
        session.asc_base = result.asc_base

        return {
            "trace_path": session.trace_path,
            "dbc_paths": session.dbc_paths,
            "summary": result.summary,
            "asc_base": result.asc_base,
            "ambiguous_ids": {hex(k): v for k, v in result.ambiguous_ids.items()},
        }

    @app.get("/api/status")
    def api_status() -> dict:
        if session.store is None:
            return {"loaded": False}
        return {
            "loaded": True,
            "trace_path": session.trace_path,
            "dbc_paths": session.dbc_paths,
            "summary": session.store.summary(),
            "ambiguous_ids": {hex(k): v for k, v in session.ambiguous_ids.items()},
        }

    @app.get("/api/signals")
    def api_signals() -> dict:
        if session.catalog is None:
            return {"signals": []}
        return {
            "signals": [
                {
                    "message_name": s.message_name,
                    "signal_name": s.signal_name,
                    "id_hex": _id_hex(s.arbitration_id, s.is_extended_id),
                    "unit": s.unit,
                    "minimum": s.minimum,
                    "maximum": s.maximum,
                    "databases": list(s.databases),
                }
                for s in session.catalog.signals()
            ]
        }

    @app.get("/api/series")
    def api_series(
        message: str,
        signal: str,
        start: float | None = None,
        end: float | None = None,
        max_points: int = 200_000,
    ) -> dict:
        store = session.require_store()
        return store.signal_series(message, signal, start, end, max_points)

    @app.get("/api/cursor")
    def api_cursor(message: str, signal: str, at: float) -> dict:
        store = session.require_store()
        sample = store.nearest_sample(message, signal, at)
        if sample is None:
            raise HTTPException(404, "No sample for that signal.")
        return sample

    @app.get("/api/trace")
    def api_trace(
        offset: int = 0,
        limit: int = 200,
        start: float | None = None,
        end: float | None = None,
        frames: bool = True,
        events: bool = True,
    ) -> dict:
        store = session.require_store()
        limit = max(1, min(limit, 2000))
        return store.trace_rows(offset, limit, start, end, frames, events)

    @app.get("/api/frame-signals")
    def api_frame_signals(at: float, id: int) -> dict:
        store = session.require_store()
        return {"signals": store.frame_signals(at, id)}

    @app.get("/")
    def index() -> FileResponse:
        return FileResponse(_WEB_DIR / "index.html")

    if _WEB_DIR.is_dir():
        app.mount("/static", StaticFiles(directory=_WEB_DIR), name="static")

    return app


def normalize_local_path(raw: str) -> str:
    """Map a pasted Windows/UNC path to the POSIX path seen inside WSL.

    The UI is typically opened from a Windows browser, so operators paste paths
    like ``\\\\wsl.localhost\\Ubuntu\\home\\paul\\trace.asc`` or ``C:\\data\\x.asc``.
    The backend runs under Linux and needs the corresponding POSIX path.
    """
    s = raw.strip().strip('"').strip("'")
    if not s:
        return s

    # UNC paths: \\wsl.localhost\<distro>\... or \\wsl$\<distro>\...
    if s.startswith(("\\\\", "//")):
        parts = [p for p in s.replace("\\", "/").split("/") if p]
        if parts and parts[0].lower() in {"wsl.localhost", "wsl$"}:
            return "/" + "/".join(parts[2:])  # drop host + distro name
        return "/" + "/".join(parts)

    # Windows drive path C:\... -> WSL mount /mnt/c/...
    drive = re.match(r"^([A-Za-z]):[\\/](.*)$", s)
    if drive:
        return f"/mnt/{drive.group(1).lower()}/{drive.group(2).replace(chr(92), '/')}"

    return s


def _id_hex(arbitration_id: int, is_extended: bool) -> str:
    width = 8 if is_extended else 3
    return f"{arbitration_id:0{width}X}"


app = create_app()
