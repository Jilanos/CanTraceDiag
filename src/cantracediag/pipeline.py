"""Orchestration: import an ASC trace, decode against DBCs, index locally."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from cantracediag.dbc import DbcCatalog
from cantracediag.decode import Decoder
from cantracediag.formats.asc import parse_asc
from cantracediag.store import TraceStore


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
) -> tuple[TraceStore, ImportResult]:
    """Parse an ASC trace, decode frames, and populate a TraceStore.

    Real trace and DBC files are read from local disk only; nothing is written
    back to the repository (AC1, AC8).
    """

    catalog = DbcCatalog()
    for dbc in dbc_paths or []:
        catalog.load(dbc)

    decoder = Decoder(catalog.message_index() if dbc_paths else None)
    parsed = parse_asc(trace_path)

    store = store or TraceStore(db_path)

    decoded_frames = []
    all_samples = []
    for frame in parsed.frames:
        updated, samples = decoder.decode_frame(frame)
        decoded_frames.append(updated)
        all_samples.extend(samples)

    store.ingest_frames(decoded_frames)
    store.ingest_events(parsed.events)
    store.ingest_samples(all_samples)

    result = ImportResult(
        trace_path=str(trace_path),
        dbc_paths=[str(p) for p in (dbc_paths or [])],
        summary=store.summary(),
        ambiguous_ids=catalog.find_ambiguous_ids(),
        asc_base=parsed.base,
    )
    return store, result
