"""Orchestration: import an ASC trace, decode against DBCs, index locally."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from cantracediag.dbc import DbcCatalog
from cantracediag.decode import Decoder
from cantracediag.formats.asc import stream_asc
from cantracediag.models import NonDataEvent, RawCanFrame
from cantracediag.store import TraceStore

# Frames/events are ingested in bounded batches so peak memory stays flat on
# large acquisitions (AC8) instead of materializing the whole trace at once.
_BATCH = 50_000


class ImportCancelled(Exception):
    """Raised when an operator-requested cancellation interrupts an import."""


@dataclass(slots=True)
class ImportResult:
    trace_path: str
    dbc_paths: list[str]
    summary: dict
    ambiguous_ids: dict[int, list[str]]
    asc_base: str


def import_trace(
    trace_path: str | Path,
    dbc_paths: list[str | Path] | None = None,
    db_path: str = ":memory:",
    store: TraceStore | None = None,
    resolution: dict[int, str] | None = None,
    catalog: DbcCatalog | None = None,
    unresolved_ambiguous_ids: set[int] | None = None,
    on_progress: Callable[[float], None] | None = None,
    cancel_check: Callable[[], bool] | None = None,
    decode_samples: bool = False,
) -> tuple[TraceStore, ImportResult]:
    """Parse an ASC trace, decode frames, and populate a TraceStore.

    Real trace and DBC files are read from local disk only; nothing is written
    back to the repository (AC1, AC8). ``resolution`` maps an arbitration id to
    the DBC name that should own it when several DBCs conflict (AC10). A
    prebuilt ``catalog`` may be passed to avoid reloading DBC files.

    ``on_progress`` is called with a fraction in ``[0, 1]`` estimated from the
    bytes of the trace file consumed so far. ``cancel_check``, when given, is
    polled once per item; if it returns ``True`` the import stops and raises
    :class:`ImportCancelled` (a store created internally by this call is
    closed before the exception propagates; a caller-supplied ``store`` is
    left open for the caller to handle).
    """

    if catalog is None:
        catalog = DbcCatalog()
        for dbc in dbc_paths or []:
            catalog.load(dbc)

    has_db = bool(catalog.databases)
    decoder = Decoder(
        catalog.message_index() if has_db else None,
        resolution,
        unresolved_ambiguous_ids,
    )

    owns_store = store is None
    store = store or TraceStore(db_path)

    frame_batch: list[RawCanFrame] = []
    sample_batch: list = []
    event_batch: list[NonDataEvent] = []
    frames_seen = 0
    events_seen = 0

    def flush() -> None:
        nonlocal frames_seen, events_seen
        if frame_batch:
            store.ingest_frames(frame_batch, seq_start=frames_seen)
            frames_seen += len(frame_batch)
            frame_batch.clear()
        if sample_batch:
            for start in range(0, len(sample_batch), _BATCH):
                store.ingest_samples(sample_batch[start:start + _BATCH])
            sample_batch.clear()
        if event_batch:
            store.ingest_events(event_batch, seq_start=events_seen)
            events_seen += len(event_batch)
            event_batch.clear()

    try:
        total_bytes = Path(trace_path).stat().st_size
    except OSError:
        total_bytes = 0

    def _report(pos: int) -> None:
        if on_progress is None:
            return
        frac = min(1.0, pos / total_bytes) if total_bytes else 0.0
        on_progress(frac)

    try:
        scanner, items = stream_asc(trace_path, on_progress=_report if on_progress else None)
        for item in items:
            if cancel_check is not None and cancel_check():
                raise ImportCancelled("Import cancelled by operator.")
            if isinstance(item, RawCanFrame):
                if decode_samples:
                    updated, samples = decoder.decode_frame(item)
                else:
                    updated, _ = decoder.describe_frame(item)
                    samples = []
                frame_batch.append(updated)
                sample_batch.extend(samples)
            else:
                event_batch.append(item)
            if (
                len(frame_batch) >= _BATCH
                or len(event_batch) >= _BATCH
                or len(sample_batch) >= _BATCH
            ):
                flush()
        flush()
    except Exception:
        if owns_store:
            store.close()
        raise

    result = ImportResult(
        trace_path=str(trace_path),
        dbc_paths=[str(p) for p in (dbc_paths or [])],
        summary=store.summary(),
        ambiguous_ids=catalog.find_ambiguous_ids(),
        asc_base=scanner.base,
    )
    return store, result
