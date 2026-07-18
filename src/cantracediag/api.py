"""Local query API and static UI host for CanTraceDiag.

The API holds a single in-process acquisition (one CAN bus, MVP scope) and
serves bounded queries so the browser never loads the whole trace (AC4-AC6,
AC8). It is local-first: it binds to localhost by default. Traces and DBCs are
supplied either as uploads from the browser's native file picker
(``/api/import-files``) or as server-side paths (``/api/import``, for the CLI).
"""

from __future__ import annotations

import os
import re
import shutil
import tempfile
import threading
import uuid
from contextlib import contextmanager
from pathlib import Path

import cantools
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from starlette.concurrency import run_in_threadpool

from cantracediag import export
from cantracediag.dbc import DbcCatalog
from cantracediag.decode import Decoder
from cantracediag.models import DecodedSignalSample
from cantracediag.pipeline import ImportCancelled, import_trace
from cantracediag.security import SecurityConfig
from cantracediag.store import TraceStore, _id_hex
from cantracediag.workspace import Workspace

_WEB_DIR = Path(__file__).parent / "web"
_TOKEN_HEADER = "x-ctd-token"


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
        self.workspace: Workspace | None = None
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


class ExportSignal(BaseModel):
    message: str
    signal: str


class CursorBatchRequest(BaseModel):
    signals: list[ExportSignal] = []
    a: float | None = None
    b: float | None = None


class ExportRequest(BaseModel):
    signals: list[ExportSignal] = []
    # "between_ab" and "visible" require start/end; "full" ignores them.
    scope: str = "between_ab"
    start: float | None = None
    end: float | None = None
    # "csv" and "parquet" use the canonical long schema; "csv_wide" pivots by
    # timestamp without interpolation.
    format: str = "csv"


_EXPORT_FORMATS = {
    "csv": ("text/csv", "csv"),
    "csv_wide": ("text/csv", "csv"),
    "parquet": ("application/vnd.apache.parquet", "parquet"),
}


def create_app(
    workspace: Workspace | None = None,
    security: SecurityConfig | None = None,
) -> FastAPI:
    app = FastAPI(title="CanTraceDiag", version="0.1.0")
    session = Session()
    session.workspace = workspace or Workspace.from_env()
    cfg = security or SecurityConfig.from_env()
    # Exposed so a test (or an embedding process) can reach the live session,
    # e.g. to close the store connection when simulating a server restart, and
    # read the per-process session token.
    app.state.ctd_session = session
    app.state.ctd_security = cfg

    @app.middleware("http")
    async def _guard(request: Request, call_next):
        # DNS-rebinding and cross-site defences run before any handler (AC10).
        if not cfg.host_allowed(request.headers.get("host")):
            return JSONResponse({"detail": "Host not allowed."}, status_code=403)
        if not cfg.origin_allowed(request.headers.get("origin")):
            return JSONResponse({"detail": "Origin not allowed."}, status_code=403)
        if cfg.requires_token(request.url.path, request.method):
            provided = request.headers.get(_TOKEN_HEADER) or request.query_params.get("token")
            if not cfg.token_ok(provided):
                return JSONResponse(
                    {"detail": "Missing or invalid session token."}, status_code=401
                )
        return await call_next(request)

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
        db_path, db_tmpdir = session.workspace.new_analysis_holder()

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
        db_path, db_tmpdir = session.workspace.new_analysis_holder()

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
        # Persist to the workspace so a later restart restores this analysis
        # without re-parsing the ASC (best-effort: a failed workspace write must
        # not discard the already-successful in-session import).
        try:
            entries = [
                session.workspace.store_dbc(path, disp)
                for path, disp in zip(dbcs, display_dbcs, strict=False)
            ]
            session.workspace.commit_analysis(
                db_tmpdir,
                trace_display=display_trace,
                asc_base=result.asc_base,
                dbcs=entries,
                resolution=resolution,
            )
        except Exception as exc:  # noqa: BLE001 - persistence is best-effort
            print(f"[cantracediag] workspace persist failed: {exc}")
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

    def _decoder() -> Decoder:
        if session.catalog is None:
            raise HTTPException(status_code=409, detail="No DBC loaded.")
        unresolved = set(session.ambiguous_ids) - set(session.resolution)
        return Decoder(
            session.catalog.message_index(),
            session.resolution,
            unresolved,
        )

    def _signal_info(message: str, signal: str):
        if session.catalog is None:
            raise HTTPException(status_code=409, detail="No DBC loaded.")
        for info in session.catalog.signals():
            if info.message_name == message and info.signal_name == signal:
                return info
        raise HTTPException(404, "No such signal in loaded DBC.")

    def _signal_ids_matching(term: str | None) -> list[int] | None:
        if not term or session.catalog is None:
            return None
        needle = term.lower()
        ids = {
            info.arbitration_id
            for info in session.catalog.signals()
            if needle in info.signal_name.lower()
        }
        return sorted(ids)

    def _sample_payload(sample: DecodedSignalSample) -> dict:
        value = sample.value
        return {
            "signal_name": sample.signal_name,
            "value_num": value if isinstance(value, (int, float)) else None,
            "value_text": value if isinstance(value, str) else None,
            "unit": sample.unit,
        }

    def _ensure_series_cached(
        store: TraceStore,
        message: str,
        signal: str,
        start: float | None,
        end: float | None,
    ) -> None:
        if store.has_series_cache(message, signal, start, end):
            return
        info = _signal_info(message, signal)
        decoder = _decoder()
        samples: list[DecodedSignalSample] = []
        frames = store.frames_for_signal(info.arbitration_id, start, end)
        for frame in frames:
            sample = decoder.decode_signal(frame, message, signal)
            if sample is not None:
                samples.append(sample)
        store.replace_signal_samples(message, signal, samples, start, end)
        store.mark_series_cached(message, signal, start, end, len(frames), len(samples))

    @app.post("/api/import")
    def api_import(req: ImportRequest) -> dict:
        """Import by server-side path (CLI/power users; accepts Windows/UNC paths).

        Reading an arbitrary server path is disabled outside loopback unless
        explicitly re-enabled, so ``--lan`` never exposes the filesystem (AC11).
        Error messages never echo the resolved local path (AC10).
        """
        if not cfg.allow_server_import:
            raise HTTPException(403, "Server-side path import is disabled.")
        trace = Path(normalize_local_path(req.trace_path)).expanduser()
        if not trace.is_file():
            raise HTTPException(404, "Trace file not found.")
        dbc_paths = [Path(normalize_local_path(d)).expanduser() for d in req.dbc_paths]
        for dbc in dbc_paths:
            if not dbc.is_file():
                raise HTTPException(404, "DBC file not found.")
        try:
            return _prepare(
                trace, dbc_paths, str(trace), [str(p) for p in dbc_paths],
                _parse_resolution(req.resolution), tmpdir=None,
            )
        except ImportCancelled as exc:
            raise HTTPException(409, str(exc)) from exc

    @app.post("/api/import-files")
    async def api_import_files(
        request: Request,
        trace: UploadFile = File(...),
        dbcs: list[UploadFile] = File(default=[]),
        library: list[str] = Form(default=[]),
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

        # Reject oversized uploads early via the declared length, then enforce
        # the cap while streaming so a lying Content-Length cannot bypass it (AC10).
        declared = request.headers.get("content-length")
        if declared is not None and declared.isdigit() and int(declared) > cfg.max_upload_bytes:
            raise HTTPException(413, "Upload exceeds the configured size limit.")

        tmpdir = Path(tempfile.mkdtemp(prefix="ctd_"))
        keep_tmpdir = False
        try:
            trace_path = tmpdir / _safe_name(trace.filename)
            await _spool(trace, trace_path, cfg.max_upload_bytes)

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
                await _spool(upload, dest, cfg.max_upload_bytes)
                dbc_paths.append(dest)
                display_dbcs.append(Path(name).name)

            # DBCs picked from the persistent library (AC5): no re-upload; the
            # library file lives outside tmpdir, so tmpdir cleanup never touches
            # it. Skip any whose basename a fresh upload already provided.
            for digest in library:
                lib_path = session.workspace.library_path(digest)
                if lib_path is None:
                    raise HTTPException(400, f"Unknown library DBC: {digest}")
                safe = _safe_name(lib_path.name)
                if safe in seen_names:
                    continue
                seen_names.add(safe)
                dbc_paths.append(lib_path)
                display_dbcs.append(lib_path.name)

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

    @app.get("/api/dbc-library")
    def api_dbc_library() -> dict:
        """List DBC files kept in the persistent library (AC4)."""
        return {
            "dbcs": [
                {"digest": e.digest, "name": e.name, "last_used": e.last_used}
                for e in session.workspace.library()
            ],
            # Basenames so the UI can pre-select last-session DBCs regardless of
            # whether they were uploaded (basename) or imported by path (full).
            "last_session": [Path(p).name for p in session.dbc_paths],
        }

    @app.post("/api/workspace-purge")
    def api_workspace_purge() -> dict:
        """Clear the DBC library and the last analysis, and drop the session (AC8)."""
        session.clear_store()
        session.clear_pending()
        session.catalog = None
        session.trace_path = None
        session.dbc_paths = []
        session.ambiguous_ids = {}
        session.resolution = {}
        session.asc_base = None
        session.last_job = None
        session.workspace.purge()
        return {"purged": True}

    @app.get("/api/signals")
    def api_signals() -> dict:
        if session.catalog is None:
            return {"signals": []}
        present: set = set()
        present_ids: set[int] = set()
        try:
            with session.use_store() as store:
                present = store.present_signal_keys()
                present_ids = store.present_arbitration_ids()
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
                    "present": (
                        (s.message_name, s.signal_name, s.arbitration_id) in present
                        or s.arbitration_id in present_ids
                    ),
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
            _ensure_series_cached(store, message, signal, start, end)
            return store.signal_series(message, signal, start, end, max_points)

    def _resolve_cursor(store: TraceStore, message: str, signal: str, at: float):
        """Nearest sample for one signal at ``at`` (AC8): a cached sample if
        present, else the signal decoded from the nearest frame on demand."""
        sample = store.nearest_sample(message, signal, at)
        if sample is not None:
            return sample
        info = _signal_info(message, signal)
        frame = store.nearest_frame_for_signal(info.arbitration_id, at)
        decoded = _decoder().decode_signal(frame, message, signal) if frame else None
        if decoded is None:
            return None
        return {
            "timestamp_s": decoded.timestamp_s,
            "value": decoded.value,
            "unit": decoded.unit,
        }

    @app.get("/api/cursor")
    def api_cursor(message: str, signal: str, at: float) -> dict:
        with session.use_store() as store:
            sample = _resolve_cursor(store, message, signal, at)
        if sample is None:
            raise HTTPException(404, "No sample for that signal.")
        return sample

    @app.post("/api/cursors")
    def api_cursors(req: CursorBatchRequest) -> dict:
        """Nearest values for N signals at cursors A and B in one call (AC8).

        Collapses the per-signal, per-cursor round-trips the readout used to fire
        into a single bounded request; each lookup stays two bounded queries.
        """
        with session.use_store() as store:
            out: dict[str, dict] = {}
            for label, at in (("a", req.a), ("b", req.b)):
                if at is None:
                    out[label] = {}
                    continue
                out[label] = {
                    f"{s.message}.{s.signal}": _resolve_cursor(store, s.message, s.signal, at)
                    for s in req.signals
                }
        return out

    @app.get("/api/trace")
    def api_trace(
        cursor: str | None = None,
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
            try:
                return store.trace_rows(
                    cursor, limit, start, end, frames, events,
                    id_hex=id, message=message, direction=direction,
                    decode_status=status, event_type=event_type, signal=signal,
                    signal_ids=_signal_ids_matching(signal),
                )
            except ValueError as exc:
                raise HTTPException(400, str(exc)) from exc

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
                signal_ids=_signal_ids_matching(signal),
            )

    @app.get("/api/frame-signals")
    def api_frame_signals(at: float, id: int) -> dict:
        with session.use_store() as store:
            signals = store.frame_signals(at, id)
            if signals:
                return {"signals": signals}
            frame = store.frame_at(at, id)
            if frame is None:
                return {"signals": []}
            _, samples = _decoder().decode_frame(frame)
            return {"signals": [_sample_payload(sample) for sample in samples]}

    @app.get("/api/report")
    def api_report() -> dict:
        """Import synthesis for the Report view (AC1).

        Combines the analysed file and DBC selection with the acquisition
        summary: time range and duration, volumes (frames, events, ids), the
        DBCs actually credited with a decode, and anomalies grouped by type
        (decode failures plus non-data ASC events).
        """
        with session.use_store() as store:
            summary = store.summary()
            usage = store.dbc_usage()
        status = summary.get("decode_status", {})
        start_s, end_s = summary.get("start_s"), summary.get("end_s")
        duration = (
            end_s - start_s if start_s is not None and end_s is not None else None
        )
        anomalies = {
            "unknown_id": int(status.get("unknown_id", 0) or 0),
            "ambiguous_id": int(status.get("ambiguous_id", 0) or 0),
            "decode_error": int(status.get("decode_error", 0) or 0),
            # Non-data ASC events (ErrorFrame, Status, Other, CANFD, …) are the
            # trace-level anomalies distinct from decode failures.
            "asc_events": {k: int(v) for k, v in summary.get("event_types", {}).items()},
        }
        return {
            "trace_path": session.trace_path,
            "asc_base": session.asc_base,
            "dbc_paths": session.dbc_paths,
            "dbcs_used": usage,
            "start_s": start_s,
            "end_s": end_s,
            "duration_s": duration,
            "frames": summary.get("frames", 0),
            "events": summary.get("events", 0),
            "decoded_frames": summary.get("decoded_frames", 0),
            "unique_ids": summary.get("unique_ids", 0),
            "decode_status": status,
            "anomalies": anomalies,
        }

    @app.get("/api/signal-stats")
    def api_signal_stats(
        message: str,
        signal: str,
        start: float | None = None,
        end: float | None = None,
    ) -> dict:
        """Range statistics for one signal between two bounds (AC3)."""
        with session.use_store() as store:
            _ensure_series_cached(store, message, signal, start, end)
            return store.signal_stats(message, signal, start, end)

    @app.post("/api/export")
    def api_export(req: ExportRequest) -> StreamingResponse:
        """Stream selected signals over a chosen range as CSV or Parquet (AC2).

        The export is generated incrementally from DuckDB so memory does not
        grow with the number of exported rows. ``scope`` selects the range:
        ``between_ab`` and ``visible`` use the supplied ``start``/``end``;
        ``full`` exports the whole trace.
        """
        if not req.signals:
            raise HTTPException(400, "Select at least one signal to export.")
        if req.format not in _EXPORT_FORMATS:
            raise HTTPException(400, f"Unknown export format: {req.format}")
        if req.scope not in {"between_ab", "visible", "full"}:
            raise HTTPException(400, f"Unknown export scope: {req.scope}")
        if req.scope == "full":
            start, end = None, None
        else:
            if req.start is None or req.end is None:
                raise HTTPException(400, f"Scope '{req.scope}' requires start and end.")
            start, end = min(req.start, req.end), max(req.start, req.end)

        pairs = [(s.message, s.signal) for s in req.signals]
        media_type, suffix = _EXPORT_FORMATS[req.format]

        # Hold the store for the whole response: the streaming body is consumed
        # after this function returns, so it is released in the generators'
        # finally clauses (or after the Parquet file is fully written).
        with session._lock:
            store = session.store
        if store is None or not store.acquire():
            raise HTTPException(409, "No trace loaded. POST /api/import first.")
        try:
            for message, signal in pairs:
                _ensure_series_cached(store, message, signal, start, end)
        except Exception:
            store.release()
            raise

        filename = f"cantracediag_export.{suffix}"
        headers = {"Content-Disposition": f'attachment; filename="{filename}"'}

        if req.format == "parquet":
            # Parquet needs a seekable sink, so it is written to a temp file
            # (one batch at a time, bounded memory) and then streamed out.
            fd, tmp_path = tempfile.mkstemp(prefix="ctd_export_", suffix=".parquet")
            try:
                with os.fdopen(fd, "wb") as sink:
                    export.long_parquet(
                        store.iter_export_batches(pairs, start, end), sink
                    )
            except Exception:
                os.unlink(tmp_path)
                raise
            finally:
                store.release()

            def _file_iter():
                try:
                    with open(tmp_path, "rb") as handle:
                        while chunk := handle.read(1 << 16):
                            yield chunk
                finally:
                    os.unlink(tmp_path)

            return StreamingResponse(_file_iter(), media_type=media_type, headers=headers)

        if req.format == "csv_wide":
            labels = [export.signal_label(m, s) for m, s in pairs]
            body = export.wide_csv(store.iter_export_batches(pairs, start, end), labels)
        else:
            body = export.long_csv(store.iter_export_batches(pairs, start, end))

        def _stream():
            try:
                yield from body
            finally:
                store.release()

        return StreamingResponse(_stream(), media_type=media_type, headers=headers)

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
    def index() -> HTMLResponse:
        # Embed the session token in the shell so same-origin scripts can send it
        # (AC10). Cross-origin pages cannot read this document, so the token is
        # only exposed to a legitimately served UI. In LAN mode the middleware
        # already required the token to reach this route.
        html = (_WEB_DIR / "index.html").read_text(encoding="utf-8")
        meta = f'<meta name="ctd-token" content="{cfg.token}" />'
        html = html.replace("</head>", f"{meta}\n</head>", 1)
        return HTMLResponse(html)

    @app.get("/favicon.ico", include_in_schema=False)
    def favicon() -> FileResponse:
        return FileResponse(_WEB_DIR / "app-icon.ico")

    if _WEB_DIR.is_dir():
        app.mount("/static", StaticFiles(directory=_WEB_DIR), name="static")

    # Restore the last persisted analysis so a relaunch lands straight on it,
    # without re-parsing the ASC (AC6). Best-effort and defensive: any missing,
    # corrupt or incompatible state starts empty rather than crashing (AC7).
    if not session.workspace.ephemeral:
        _restore_last_analysis(session)

    return app


def _restore_last_analysis(session: Session) -> None:
    ws = session.workspace
    try:
        manifest = ws.load_manifest()
        if not manifest:
            return
        db_path = ws.analysis_db_path(manifest)
        if db_path is None:
            return
        catalog = DbcCatalog()
        dbc_display: list[str] = []
        for entry in manifest.get("dbcs", []):
            lib_path = ws.library_path(entry.get("digest", ""))
            if lib_path is None:
                return  # a referenced library DBC is gone -> incoherent (AC7)
            catalog.load(lib_path)
            dbc_display.append(entry.get("name") or lib_path.name)
        store = TraceStore(str(db_path))
    except Exception as exc:  # noqa: BLE001 - never crash startup on bad state
        print(f"[cantracediag] could not restore last analysis: {exc}")
        return

    session.replace_store(store, db_path.parent)
    session.catalog = catalog
    session.trace_path = manifest.get("trace_display")
    session.dbc_paths = dbc_display
    session.ambiguous_ids = catalog.find_ambiguous_ids()
    session.resolution = _parse_resolution(manifest.get("resolution", {}))
    session.asc_base = manifest.get("asc_base")
    session.last_job = {
        "id": uuid.uuid4().hex, "phase": "complete", "progress": 1.0,
        "detail": "Restored last analysis.", "cancellable": False,
    }


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


async def _spool(upload: UploadFile, dest: Path, max_bytes: int | None = None) -> None:
    """Stream an uploaded file to disk in chunks (handles large traces).

    Enforces ``max_bytes`` while streaming so an upload cannot exceed the
    configured cap even if it lies about its Content-Length (AC10).
    """
    written = 0
    with open(dest, "wb") as handle:
        while chunk := await upload.read(1 << 20):
            written += len(chunk)
            if max_bytes is not None and written > max_bytes:
                await upload.close()
                raise HTTPException(413, "Upload exceeds the configured size limit.")
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


def _discard_store(tmpdir: Path) -> None:
    """Remove a store's temp directory after a failed/cancelled import.

    The store itself is already closed by ``import_trace`` (it owns any store
    it created internally); this only clears the on-disk leftovers so a
    cancelled or failed import never touches the still-active session store
    (AC3).
    """
    shutil.rmtree(tmpdir, ignore_errors=True)


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
