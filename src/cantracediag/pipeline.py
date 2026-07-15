"""Orchestration: import an ASC trace, decode against DBCs, index locally."""

from __future__ import annotations

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
) -> tuple[TraceStore, ImportResult]:
    """Parse an ASC trace, decode frames, and populate a TraceStore.

    Real trace and DBC files are read from local disk only; nothing is written
    back to the repository (AC1, AC8). ``resolution`` maps an arbitration id to
    the DBC name that should own it when several DBCs conflict (AC10). A
    prebuilt ``catalog`` may be passed to avoid reloading DBC files.
    """

    if catalog is None:
        catalog = DbcCatalog()
        for dbc in dbc_paths or []:
            catalog.load(dbc)

    has_db = bool(catalog.databases)
    decoder = Decoder(catalog.message_index() if has_db else None, resolution)

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
            store.ingest_samples(sample_batch)
            sample_batch.clear()
        if event_batch:
            store.ingest_events(event_batch, seq_start=events_seen)
            events_seen += len(event_batch)
            event_batch.clear()

    scanner, items = stream_asc(trace_path)
    for item in items:
        if isinstance(item, RawCanFrame):
            updated, samples = decoder.decode_frame(item)
            frame_batch.append(updated)
            sample_batch.extend(samples)
        else:
            event_batch.append(item)
        if len(frame_batch) >= _BATCH or len(event_batch) >= _BATCH:
            flush()
    flush()

    result = ImportResult(
        trace_path=str(trace_path),
        dbc_paths=[str(p) for p in (dbc_paths or [])],
        summary=store.summary(),
        ambiguous_ids=catalog.find_ambiguous_ids(),
        asc_base=scanner.base,
    )
    return store, result
