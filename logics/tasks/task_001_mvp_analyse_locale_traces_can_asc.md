## task_001_mvp_analyse_locale_traces_can_asc - Créer le MVP d'analyse locale de traces CAN ASC
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: Medium
> Theme: Implementation delivery
> Non-semantic edit: Added AC Traceability section (proof mapping) for audit; no scope change.
> Reminder: Update status/understanding/confidence/progress and linked request/backlog references when you edit this doc.

# Definition of Done (DoD)
- [x] The backlog scope is implemented.
- [x] Acceptance criteria are covered.
- [x] Validation passes.
- [x] Meaningful waves followed ADR 009: affected docs updated and the repo left commit-ready without automatic commits.

# Backlog
- `item_001_mvp_analyse_locale_traces_can_asc`

# Acceptance criteria
- AC1: The user can import a local ASC trace without committing it to the repository.
- AC2: The user can load multiple local DBC files and inspect available messages/signals.
- AC3: The MVP decodes supported frames into physical signal samples while preserving raw frames and decode failures.
- AC4: The graph view displays selected signals as stacked subplots with a shared time axis.
- AC5: Cursor values use the nearest sample; no interpolation is used.
- AC6: The trace view shows raw CAN frames, decoded message names/signals where available, and non-data events.
- AC7: The trace view has a path toward configurable columns: visibility, order, width, and display format.
- AC8: The implementation remains local-first and does not require replay controls.

# Validation
- Run `logics-manager lint --require-status`.
- Use `logics-manager flow progress task task_001_mvp_analyse_locale_traces_can_asc --progress <n>%` during multi-wave work.
- Run `logics-manager flow finish task task_001_mvp_analyse_locale_traces_can_asc` after implementation.
- Finish workflow executed on 2026-07-15.
- Linked backlog/request close verification passed.

# Report
- Implementation complete. Delivered the full MVP chain: ASC ingestion, multi-DBC
- Finished on 2026-07-15.
- Linked backlog item(s): `item_001_mvp_analyse_locale_traces_can_asc`
- Related request(s): `req_000_mvp_analyse_locale_traces_can_asc`
  loading with ambiguous-ID detection, DBC decoding into physical samples, a local
  DuckDB index with windowed queries, a FastAPI query API, a Typer CLI, and a local
  web UI (stacked subplots + configurable trace view).
- AC coverage:
  - AC1 — `POST /api/import` / `cantracediag info` read local `.asc` paths only; nothing
    is written to the repo (traces/DBC stay git-ignored).
  - AC2 — `DbcCatalog.load` accepts multiple DBCs; `/api/signals` and `cantracediag
    signals` list messages/signals; `find_ambiguous_ids` surfaces cross-DBC ID overlaps.
  - AC3 — `Decoder.decode_frame` produces `DecodedSignalSample`s while preserving every
    raw frame and stamping `decode_status` (ok/unknown_id/no_database/decode_error).
  - AC4 — web UI renders one stacked subplot per selected signal on a shared time axis.
  - AC5 — cursor uses nearest stored sample (client-side nearest-index and
    `store.nearest_sample`); no interpolation. Plots drawn as sample-and-hold steps.
  - AC6 — `/api/trace` merges raw frames, decoded names, and non-data events
    (ErrorFrame, Status) in a time-ordered paginated view; row click shows decoded signals.
  - AC7 — trace columns support visibility, order (drag), width, and display format,
    persisted in localStorage.
  - AC8 — local-first (binds 127.0.0.1) with no replay controls.
- Validation: `logics-manager lint --require-status` OK; 22 pytest tests pass; ruff clean.
  End-to-end server flow verified via live HTTP; 200k-frame scale check imported in ~3.3s
  with millisecond windowed queries.
- Environment note: system Python packaging was broken (no ensurepip/pip/venv). Deps were
  bootstrapped into a git-ignored `.pydeps/` via a standalone pip; run tests/tools with
  `PYTHONPATH=.pydeps:src`. A normal `pip install -e ".[dev,api]"` works once venv is available.

# AC Traceability
- AC1 -> Local ASC import. Proof: `POST /api/import` / `cantracediag info` read local `.asc` paths only; traces/DBC stay git-ignored.
- AC2 -> Multi-DBC inspection. Proof: `DbcCatalog.load` accepts multiple DBCs; `/api/signals` lists messages/signals; `find_ambiguous_ids` surfaces overlaps.
- AC3 -> Decode with preservation. Proof: `Decoder.decode_frame` emits `DecodedSignalSample`s and stamps `decode_status`, keeping every raw frame.
- AC4 -> Stacked subplots. Proof: web UI renders one band per selected signal on a shared time axis.
- AC5 -> Nearest-sample cursor. Proof: `store.nearest_sample` + client nearest-index; no interpolation, sample-and-hold rendering.
- AC6 -> Trace view. Proof: `/api/trace` merges raw frames, decoded names, and non-data events (ErrorFrame, Status) time-ordered and paginated.
- AC7 -> Configurable columns. Proof: trace columns support visibility, order, width, and format, persisted in localStorage.
- AC8 -> Local-first. Proof: server binds 127.0.0.1 with no replay controls.

# AI Context
- Summary: Implement créer le mvp d'analyse locale de traces can asc.
- Keywords: task, implementation, backlog, runtime, python
- Use when: You need a bounded implementation task for a backlog item.
- Skip when: The work is still at the request or backlog shaping stage.

# Links
- Request: `req_000_mvp_analyse_locale_traces_can_asc`
- Product brief(s): `prod_002_product_brief_cantracediag_mvp`
- Architecture decision(s): `adr_002_adr_architecture_cantracediag_mvp`
