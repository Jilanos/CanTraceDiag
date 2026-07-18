## task_017_deliver_diagnostic_report_statistics_and_exports - Deliver diagnostic report statistics and exports
> From version: 0.1.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: Medium
> Theme: Implementation delivery
> Reminder: Update status/understanding/confidence/progress and linked request/backlog references when you edit this doc.

# Definition of Done (DoD)
- [x] The backlog scope is implemented.
- [x] Acceptance criteria are covered.
- [x] Validation passes.
- [x] Implementation, tests and documentation are delivered together in one dedicated commit for this task.

# Delivery order and commit boundary
- Sequence: 1 of 7; this is the first implementation task.
- Commit only AC1-AC3 and their tests/docs; do not include work from tasks 018-023.
- Suggested commit: `feat(diagnostic): add report statistics and exports`.

# Backlog
- `item_017_deliver_diagnostic_report_statistics_and_exports`

# Acceptance criteria
- AC1: Une vue `Report` fournit une synthese de l'import avec le fichier analyse, la
- AC2: L'utilisateur exporte en CSV et Parquet les signaux selectionnes sur la plage
- AC3: La vue `Analysis` affiche par signal numerique selectionne le nombre

# Validation
- Run focused backend/API/export tests, including bounded-memory export coverage.
- Run the full Python suite and `ruff check .`.
- Run `python3 -m logics_manager lint --require-status`.
- Use `python3 -m logics_manager flow progress task task_017_deliver_diagnostic_report_statistics_and_exports.md --progress <n>%` during multi-wave work.
- Run `python3 -m logics_manager flow finish task task_017_deliver_diagnostic_report_statistics_and_exports.md` after implementation.
- Finish workflow executed on 2026-07-18.
- Linked backlog/request close verification passed.

# Report
- Implementation complete.
- AC1 — Report synthesis: `GET /api/report` (`src/cantracediag/api.py`) combines the
- Finished on 2026-07-18.
- Linked backlog item(s): `item_017_deliver_diagnostic_report_statistics_and_exports`
- Related request(s): `req_007_finaliser_workflow_diagnostic_et_clarifier_cantracediag`
  analysed file, time range/duration, volumes (frames/events/ids), DBCs actually used
  (`TraceStore.dbc_usage`, `src/cantracediag/store.py`) and anomalies grouped by type
  (unknown_id, ambiguous_id, decode_error, ASC events). Surfaced via the "Report"
  dialog in `web/index.html`/`web/app.js`. Proof: `tests/test_export.py::test_report_endpoint`,
  `::test_report_requires_loaded_trace`.
- AC2 — Streamed export: `POST /api/export` streams the selected signals over
  `between_ab`/`visible`/`full` scopes as long CSV, long Parquet, or optional wide CSV
  (`src/cantracediag/export.py`, `TraceStore.iter_export_batches`). The export dialog in
  `web/app.js` downloads via blob. Bounded memory is proven by
  `tests/test_export.py::test_export_batches_are_memory_bounded` (resident rows capped at
  batch size for 200k rows) and `::test_export_csv_formatter_peak_is_flat`; format/scope
  coverage via `::test_export_endpoint_csv`, `::test_export_endpoint_parquet`,
  `::test_export_long_parquet_roundtrip`, `::test_export_wide_csv_does_not_interpolate`.
- AC3 — Range statistics: `GET /api/signal-stats` and `TraceStore.signal_stats` report
  count/min/max/mean/std/RMS for numeric signals and value distribution for text/enum
  signals between A and B, with explicit empty-range handling. Rendered in the range
  statistics table (`web/app.js` `refreshStats`). Proof:
  `tests/test_export.py::test_signal_stats_numeric`, `::test_signal_stats_text_distribution`,
  `::test_signal_stats_window_bounds`, `::test_signal_stats_empty_window_is_explicit`,
  `::test_signal_stats_endpoint`.
- Validation: `ruff check .` clean; full suite `89 passed, 11 skipped` (Chromium E2E) in an
  isolated `uv` environment. The tab restructure (AC4) stays out of scope per `item_023`.

# AI Context
- Summary: Implement deliver diagnostic report statistics and exports.
- Keywords: task, implementation, backlog, runtime, python
- Use when: You need a bounded implementation task for a backlog item.
- Skip when: The work is still at the request or backlog shaping stage.

# Links
- Request: `req_007_finaliser_workflow_diagnostic_et_clarifier_cantracediag`
- Product brief(s): (none yet)
- Architecture decision(s): (none yet)
