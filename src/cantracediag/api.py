"""Local query API and static UI host for CanTraceDiag.

The API holds a single in-process acquisition (one CAN bus, MVP scope) and
serves bounded queries so the browser never loads the whole trace (AC4-AC6,
AC8). It is local-first: it binds to localhost by default. Traces and DBCs are
supplied either as uploads from the browser's native file picker
(``/api/import-files``) or as server-side paths (``/api/import``, for the CLI).
"""

from __future__ import annotations

import re
import shutil
import tempfile
import threading
import uuid
from contextlib import contextmanager
from pathlib import Path

import cantools
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from starlette.concurrency import run_in_threadpool

from cantracediag.dbc import DbcCatalog
from cantracediag.pipeline import ImportCancelled, import_trace
from cantracediag.store import TraceStore

_WEB_DIR = Path(__file__).parent / "web"


class Pending:
    """A parsed-but-not-finalized load awaiting DBC conflict resolution (AC10)."""

    def __init__(
        self,
        trace: Path,
        catalog: DbcCatalog,
        dbc_paths: list[Path],
        display_trace: str,
        display_dbcs: list[str],
        ambiguous_ids: dict[int, list[str]],
        tmpdir: Path | None,
    ) -> None:
        self.trace = trace
        self.catalog = catalog
        self.dbc_paths = dbc_paths
        self.display_trace = display_trace
        self.display_dbcs = display_dbcs
        self.ambiguous_ids = ambiguous_ids
        self.tmpdir = tmpdir

    def cleanup(self) -> None:
        if self.tmpdir is not None:
            shutil.rmtree(self.tmpdir, ignore_errors=True)
            self.tmpdir = None


_TERMINAL_JOB_PHASES = {"complete", "failed", "cancelling", "cancelled"}


class Session:
    """Holds the currently loaded acquisition.

    Session-level mutations (swapping the store, taking/clearing a pending
    conflict resolution) go through ``_lock`` so a request reading session
    state never observes a half-updated session (R-01). The store itself is
    reference-counted (see :class:`TraceStore`) so replacing it never closes
    the connection under an in-flight query (AC3): the old store is only
    actually closed, and its temp directory removed, once every request that
    had already acquired it has released it.
    """

    def __init__(self) -> None:
        self.store: TraceStore | None = None
        self.catalog: DbcCatalog | None = None
        self.trace_path: str | None = None
        self.dbc_paths: list[str] = []
        self.ambiguous_ids: dict[int, list[str]] = {}
        self.resolution: dict[int, str] = {}
        self.asc_base: str | None = None
        self.pending: Pending | None = None
        self.db_tmpdir: Path | None = None
        self.last_job: dict | None = None
        self.cancel_event: threading.Event | None = None
        self._lock = threading.Lock()

    @contextmanager
    def use_store(self):
        """Borrow the active store for the duration of one request (AC3).

        Raises 409 if no trace is loaded, or if the store was just swapped
        out (acquire() failing) rather than crashing on a closed connection.
        """
        with self._lock:
            store = self.store
        if store is None or not store.acquire():
            raise HTTPException(status_code=409, detail="No trace loaded. POST /api/import first.")
        try:
            yield store
        finally:
            store.release()

    def clear_pending(self) -> None:
        if self.pending is not None:
            self.pending.cleanup()
            self.pending = None

    def replace_store(self, store: TraceStore, tmpdir: Path | None) -> None:
        """Swap in a newly built store, deferring the old one's teardown
        until no in-flight request still holds it (AC3)."""
        with self._lock:
            old_store, old_tmpdir = self.store, self.db_tmpdir
            self.store = store
            self.db_tmpdir = tmpdir
        if old_store is not None:
            def _cleanup_old() -> None:
                if old_tmpdir is not None:
                    shutil.rmtree(old_tmpdir, ignore_errors=True)
            old_store.close(on_closed=_cleanup_old)

    def clear_store(self) -> None:
        with self._lock:
            store, tmpdir = self.store, self.db_tmpdir
            self.store = None
            self.db_tmpdir = None
        if store is not None:
            def _cleanup() -> None:
                if tmpdir is not None:
                    shutil.rmtree(tmpdir, ignore_errors=True)
            store.close(on_closed=_cleanup)

    def job(self, phase: str, progress: float, detail: str | None = None) -> None:
        self.last_job = {
            "id": self.last_job["id"] if self.last_job else uuid.uuid4().hex,
            "phase": phase,
            "progress": progress,
            "detail": detail,
            "cancellable": phase not in _TERMINAL_JOB_PHASES,
        }


class ImportRequest(BaseModel):
    trace_path: str
    dbc_paths: list[str] = []
    resolution: dict[str, str] = {}


class ResolveRequest(BaseModel):
    resolution: dict[str, str] = {}


def create_app() -> FastAPI:
    app = FastAPI(title="CanTraceDiag", version="0.1.0")
    session = Session()

    def _prepare(
        trace: Path,
        dbcs: list[Path],
        display_trace: str,
        display_dbcs: list[str],
        resolution: dict[int, str],
        tmpdir: Path | None,
    ) -> dict:
        """Load DBCs, detect conflicts, and either finalize or ask the operator.

        Conflict resolution happens *before* the (potentially long) decode so
        the operator picks which DBC owns each conflicting id first (AC10).
        Runs on a worker thread (see callers): decoding a large trace must
        never block the event loop, so ``/api/import-job`` and
        ``/api/import-cancel`` stay responsive while this runs (AC1).
        """
        session.clear_pending()
        cancel_event = threading.Event()
        session.cancel_event = cancel_event
        session.last_job = {"id": uuid.uuid4().hex, "phase": "loading_dbc", "progress": 0.02}
        _ensure_unique_basenames(dbcs)

        catalog = DbcCatalog()
        try:
            for dbc in dbcs:
                catalog.load(dbc)
        except (cantools.database.errors.Error, OSError, ValueError) as exc:
            session.job("failed", 1.0, f"Invalid DBC: {exc}")
            raise HTTPException(400, f"Invalid DBC: {exc}") from exc
        ambiguous = catalog.find_ambiguous_ids()
        _validate_resolution(catalog, ambiguous, resolution, require_complete=False)

        unresolved = [k for k in ambiguous if k not in resolution]
        if unresolved:
            session.pending = Pending(
                trace, catalog, dbcs, display_trace, display_dbcs, ambiguous, tmpdir
            )
            preview = _preview_unresolved(
                trace, catalog, dbcs, display_trace, display_dbcs, ambiguous, unresolved,
                cancel_event,
            )
            return {
                **preview,
                "needs_resolution": True,
                "conflicts": _conflicts_payload(catalog, ambiguous),
            }

        return _finalize(
            trace, catalog, dbcs, display_trace, display_dbcs, ambiguous, resolution,
            cancel_event,
        )

    def _preview_unresolved(
        trace: Path,
        catalog: DbcCatalog,
        dbcs: list[Path],
        display_trace: str,
        display_dbcs: list[str],
        ambiguous: dict[int, list[str]],
        unresolved: list[int],
        cancel_event: threading.Event,
    ) -> dict:
        # The previous session's store stays untouched until this new store
        # has actually finished importing (AC3): only replace_store() at the
        # end swaps it in, and only after import_trace() has succeeded.
        db_path, db_tmpdir = _new_store_path()

        def _progress(frac: float) -> None:
            session.job("indexing_unambiguous", 0.05 + 0.85 * frac)

        session.job("indexing_unambiguous", 0.05)
        try:
            store, result = import_trace(
                trace,
                dbcs,
                db_path=db_path,
                resolution={},
                catalog=catalog,
                unresolved_ambiguous_ids=set(unresolved),
                on_progress=_progress,
                cancel_check=cancel_event.is_set,
            )
        except ImportCancelled:
            _discard_store(db_tmpdir)
            session.job("cancelled", 1.0, "Import cancelled by operator.")
            raise
        except Exception as exc:
            _discard_store(db_tmpdir)
            session.job("failed", 1.0, str(exc))
            raise

        session.replace_store(store, db_tmpdir)
        session.catalog = catalog
        session.trace_path = display_trace
        session.dbc_paths = display_dbcs
        session.ambiguous_ids = ambiguous
        session.resolution = {}
        session.asc_base = result.asc_base
        session.job("awaiting_resolution", 0.95)

        return {
            "trace_path": session.trace_path,
            "dbc_paths": session.dbc_paths,
            "summary": result.summary,
            "asc_base": result.asc_base,
            "ambiguous_ids": {hex(k): v for k, v in ambiguous.items()},
            "resolution": {},
        }

    def _finalize(
        trace: Path,
        catalog: DbcCatalog,
        dbcs: list[Path],
        display_trace: str,
        display_dbcs: list[str],
        ambiguous: dict[int, list[str]],
        resolution: dict[int, str],
        cancel_event: threading.Event,
    ) -> dict:
        db_path, db_tmpdir = _new_store_path()

        def _progress(frac: float) -> None:
            session.job("indexing", 0.05 + 0.9 * frac)

        session.job("indexing", 0.05)
        try:
            store, result = import_trace(
                trace, dbcs, db_path=db_path, resolution=resolution, catalog=catalog,
                on_progress=_progress, cancel_check=cancel_event.is_set,
            )
        except ImportCancelled:
            _discard_store(db_tmpdir)
            session.job("cancelled", 1.0, "Import cancelled by operator.")
            raise
        except Exception as exc:
            _discard_store(db_tmpdir)
            session.job("failed", 1.0, str(exc))
            raise

        session.replace_store(store, db_tmpdir)
        session.catalog = catalog
        session.trace_path = display_trace
        session.dbc_paths = display_dbcs
        session.ambiguous_ids = ambiguous
        session.resolution = resolution
        session.asc_base = result.asc_base
        session.job("complete", 1.0)

        return {
            "needs_resolution": False,
            "trace_path": session.trace_path,
            "dbc_paths": session.dbc_paths,
            "summary": result.summary,
            "asc_base": result.asc_base,
            "ambiguous_ids": {hex(k): v for k, v in ambiguous.items()},
            "resolution": {hex(k): v for k, v in resolution.items()},
        }

    @app.post("/api/import")
    def api_import(req: ImportRequest) -> dict:
        """Import by server-side path (CLI/power users; accepts Windows/UNC paths)."""
        trace = Path(normalize_local_path(req.trace_path)).expanduser()
        if not trace.is_file():
            raise HTTPException(404, f"Trace not found: {trace}")
        dbc_paths = [Path(normalize_local_path(d)).expanduser() for d in req.dbc_paths]
        for dbc in dbc_paths:
            if not dbc.is_file():
                raise HTTPException(404, f"DBC not found: {dbc}")
        try:
            return _prepare(
                trace, dbc_paths, str(trace), [str(p) for p in dbc_paths],
                _parse_resolution(req.resolution), tmpdir=None,
            )
        except ImportCancelled as exc:
            raise HTTPException(409, str(exc)) from exc

    @app.post("/api/import-files")
    async def api_import_files(
        trace: UploadFile = File(...),
        dbcs: list[UploadFile] = File(default=[]),
    ) -> dict:
        """Import from files uploaded via the browser's native picker.

        The browser sends file *contents* (it never exposes real paths), so the
        UI works regardless of where the backend runs (e.g. WSL). Uploads land
        in a temporary directory that is removed once the acquisition is indexed
        in memory, or once conflict resolution finalizes the load; nothing is
        written into the repository (AC1, AC8).

        Decoding runs on a worker thread via ``run_in_threadpool`` instead of
        directly in this coroutine: without it, a large trace would freeze the
        whole event loop for the duration of the import, and no other request
        (including ``/api/import-job`` polling and ``/api/import-cancel``)
        could be served in the meantime (AC1).
        """
        if not (trace.filename or "").lower().endswith(".asc"):
            raise HTTPException(400, "Trace file must be a .asc file.")

        tmpdir = Path(tempfile.mkdtemp(prefix="ctd_"))
        keep_tmpdir = False
        try:
            trace_path = tmpdir / _safe_name(trace.filename)
            await _spool(trace, trace_path)

            dbc_paths: list[Path] = []
            display_dbcs: list[str] = []
            seen_names: set[str] = set()
            for upload in dbcs:
                name = upload.filename or ""
                if not name.lower().endswith(".dbc"):
                    continue  # ignore non-DBC entries (e.g. from a folder pick)
                safe = _safe_name(name)
                if safe in seen_names:
                    raise HTTPException(400, f"Duplicate DBC basename: {safe}")
                seen_names.add(safe)
                dest = tmpdir / safe
                await _spool(upload, dest)
                dbc_paths.append(dest)
                display_dbcs.append(Path(name).name)

            try:
                result = await run_in_threadpool(
                    _prepare, trace_path, dbc_paths, Path(trace.filename).name,
                    display_dbcs, {}, tmpdir,
                )
            except ImportCancelled as exc:
                raise HTTPException(409, str(exc)) from exc
            # When resolution is required the temp files must survive until
            # /api/resolve finalizes the load; Pending owns cleanup then.
            keep_tmpdir = result.get("needs_resolution", False)
            return result
        finally:
            if not keep_tmpdir:
                shutil.rmtree(tmpdir, ignore_errors=True)

    @app.post("/api/resolve")
    def api_resolve(req: ResolveRequest) -> dict:
        """Finalize a pending upload using the operator's DBC choices (AC10)."""
        pending = session.pending
        if pending is None:
            raise HTTPException(409, "No load is awaiting DBC conflict resolution.")
        resolution = _parse_resolution(req.resolution)
        _validate_resolution(
            pending.catalog, pending.ambiguous_ids, resolution, require_complete=True
        )
        session.pending = None  # take ownership; _finalize / cleanup below
        cancel_event = threading.Event()
        session.cancel_event = cancel_event
        try:
            return _finalize(
                pending.trace, pending.catalog, pending.dbc_paths,
                pending.display_trace, pending.display_dbcs,
                pending.ambiguous_ids, resolution, cancel_event,
            )
        except ImportCancelled as exc:
            raise HTTPException(409, str(exc)) from exc
        finally:
            pending.cleanup()

    @app.get("/api/status")
    def api_status() -> dict:
        try:
            with session.use_store() as store:
                return {
                    "loaded": True,
                    "trace_path": session.trace_path,
                    "dbc_paths": session.dbc_paths,
                    "summary": store.summary(),
                    "ambiguous_ids": {hex(k): v for k, v in session.ambiguous_ids.items()},
                    "resolution": {hex(k): v for k, v in session.resolution.items()},
                    "event_types": store.event_types(),
                }
        except HTTPException:
            return {"loaded": False}

    @app.get("/api/signals")
    def api_signals() -> dict:
        if session.catalog is None:
            return {"signals": []}
        present: set = set()
        try:
            with session.use_store() as store:
                present = store.present_signal_keys()
        except HTTPException:
            pass
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
                    "present": (s.message_name, s.signal_name, s.arbitration_id) in present,
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
        max_points: int = 4000,
    ) -> dict:
        max_points = max(2, min(max_points, 50_000))
        with session.use_store() as store:
            return store.signal_series(message, signal, start, end, max_points)

    @app.get("/api/cursor")
    def api_cursor(message: str, signal: str, at: float) -> dict:
        with session.use_store() as store:
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
        id: str | None = None,
        message: str | None = None,
        direction: str | None = None,
        status: str | None = None,
        event_type: str | None = None,
        signal: str | None = None,
    ) -> dict:
        limit = max(1, min(limit, 2000))
        with session.use_store() as store:
            return store.trace_rows(
                offset, limit, start, end, frames, events,
                id_hex=id, message=message, direction=direction,
                decode_status=status, event_type=event_type, signal=signal,
            )

    @app.get("/api/trace-locate")
    def api_trace_locate(
        at: float,
        start: float | None = None,
        end: float | None = None,
        frames: bool = True,
        events: bool = True,
        id: str | None = None,
        message: str | None = None,
        direction: str | None = None,
        status: str | None = None,
        event_type: str | None = None,
        signal: str | None = None,
    ) -> dict:
        with session.use_store() as store:
            return store.locate_row(
                at, frames, events, start, end,
                id_hex=id, message=message, direction=direction,
                decode_status=status, event_type=event_type, signal=signal,
            )

    @app.get("/api/frame-signals")
    def api_frame_signals(at: float, id: int) -> dict:
        with session.use_store() as store:
            return {"signals": store.frame_signals(at, id)}

    @app.get("/api/import-job")
    def api_import_job() -> dict:
        return session.last_job or {
            "id": None,
            "phase": "idle",
            "progress": 0.0,
            "detail": None,
            "cancellable": False,
        }

    @app.post("/api/import-cancel")
    def api_import_cancel() -> dict:
        if not session.last_job or not session.last_job.get("cancellable"):
            return {"cancelled": False, "reason": "No cancellable import job."}
        if session.cancel_event is not None:
            session.cancel_event.set()
        session.job("cancelling", session.last_job.get("progress", 0.0),
                    "Import cancellation requested.")
        return {"cancelled": True}

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


async def _spool(upload: UploadFile, dest: Path) -> None:
    """Stream an uploaded file to disk in chunks (handles large traces)."""
    with open(dest, "wb") as handle:
        while chunk := await upload.read(1 << 20):
            handle.write(chunk)
    await upload.close()


def _safe_name(name: str) -> str:
    """Basename only, so uploaded/relative paths cannot escape the temp dir."""
    return Path(name.replace("\\", "/")).name or "upload"


def _ensure_unique_basenames(paths: list[Path]) -> None:
    seen: set[str] = set()
    for path in paths:
        name = path.name
        if name in seen:
            raise HTTPException(400, f"Duplicate DBC basename: {name}")
        seen.add(name)


def _new_store_path() -> tuple[str, Path]:
    tmpdir = Path(tempfile.mkdtemp(prefix="ctd_db_"))
    return str(tmpdir / "analysis.duckdb"), tmpdir


def _discard_store(tmpdir: Path) -> None:
    """Remove a store's temp directory after a failed/cancelled import.

    The store itself is already closed by ``import_trace`` (it owns any store
    it created internally); this only clears the on-disk leftovers so a
    cancelled or failed import never touches the still-active session store
    (AC3).
    """
    shutil.rmtree(tmpdir, ignore_errors=True)


def _id_hex(arbitration_id: int, is_extended: bool) -> str:
    width = 8 if is_extended else 3
    return f"{arbitration_id:0{width}X}"


def _parse_resolution(raw: dict[str, str]) -> dict[int, str]:
    """Map ``{id_hex: db_name}`` from the client to ``{arbitration_id: name}``."""
    out: dict[int, str] = {}
    for key, name in raw.items():
        try:
            out[int(str(key).removeprefix("0x").removeprefix("0X"), 16)] = name
        except ValueError:
            continue
    return out


def _validate_resolution(
    catalog: DbcCatalog,
    ambiguous: dict[int, list[str]],
    resolution: dict[int, str],
    require_complete: bool,
) -> None:
    if not ambiguous and resolution:
        raise HTTPException(400, "DBC resolution was provided but no conflict is pending.")

    index = catalog.message_index()
    for frame_id, db_name in resolution.items():
        if frame_id not in ambiguous:
            raise HTTPException(400, f"Unknown DBC conflict id: {hex(frame_id)}")
        allowed = {name for name, _ in index.get(frame_id, [])}
        if db_name not in allowed:
            choices = ", ".join(sorted(allowed))
            raise HTTPException(
                400,
                f"Invalid DBC choice for {hex(frame_id)}: {db_name}. Expected one of: {choices}",
            )
    if require_complete:
        missing = sorted(set(ambiguous) - set(resolution))
        if missing:
            ids = ", ".join(hex(frame_id) for frame_id in missing)
            raise HTTPException(400, f"Missing DBC resolution for: {ids}")


def _conflicts_payload(
    catalog: DbcCatalog, ambiguous: dict[int, list[str]]
) -> list[dict]:
    """Per-conflicting-id choices for the resolution modal (AC10)."""
    index = catalog.message_index()
    payload: list[dict] = []
    for frame_id in sorted(ambiguous):
        entries = index.get(frame_id, [])
        payload.append(
            {
                "id_hex": hex(frame_id),
                "options": [
                    {"database": db_name, "message": message.name}
                    for db_name, message in entries
                ],
            }
        )
    return payload


app = create_app()
