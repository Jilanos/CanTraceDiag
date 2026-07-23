## task_030_repondre_a_l_audit_code_du_23_juillet_2026 - Repondre a l audit code du 23 juillet 2026
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: Medium
> Theme: Implementation delivery
> Reminder: Update status/understanding/confidence/progress and linked request/backlog references when you edit this doc.
> Owner: codex

# Definition of Done (DoD)
- [x] H1/S1/S3 fixes are implemented with targeted regression tests.
- [x] M1/M2 fixes are implemented with deterministic edge-case coverage.
- [x] S2/S4/S5 decisions are reflected in code, docs and tests.
- [x] Low-risk cleanup findings are completed or explicitly deferred with rationale.
- [x] Acceptance criteria are covered.
- [x] Validation passes.
- [x] Meaningful waves followed ADR 009: affected docs updated and the repo left commit-ready without automatic commits.

# Backlog
- `item_029_repondre_a_l_audit_code_du_23_juillet_2026`

# Context
- Source audit: `docs/audit-code-2026-07-23.md`.
- Current audit baseline: `ruff check .` passed, 126 Python tests passed, Playwright e2e blocked locally by missing Chromium binary.
- Primary files: `src/cantracediag/api.py`, `src/cantracediag/store.py`, `src/cantracediag/security.py`, `src/cantracediag/formats/asc.py`, `src/cantracediag/cli.py`.
- Primary tests to extend: `tests/test_api.py`, `tests/test_security.py`, `tests/test_export.py`, `tests/test_trace_nav.py`, `tests/test_asc.py`.

# Plan
- [x] 1. H1: change CSV/wide export so DuckDB store locking does not span the entire HTTP stream; add a concurrency regression around slow streaming plus a concurrent store-backed endpoint.
- [x] 2. S1: introduce or reuse a sanitization helper for DBC/import exceptions; cover parse DBC errors and failed import jobs with path-leak assertions.
- [x] 3. S3: enforce an aggregate upload budget for trace plus DBC files; cover multi-file overflow and preserve existing per-file checks.
- [x] 4. M1/M2: bind `_decimate` numeric inputs, handle `nan`/`inf`/degenerate spans deliberately, and make no-match signal filters return no frames independent of lazy sample decoding.
- [x] 5. S2/S4/S5: decide minimal policy for query token, local file import scope and missing `Host`/`Origin`; update code, CLI output, README/threat model docs and tests accordingly.
- [x] 6. Low-risk cleanup: address `series_cache` purge, exact float lookup tolerance, ASC `dlc==0` fixture, duplicate `_f`, unused `iter_asc`, and streaming store helper when low-risk; otherwise record explicit deferrals.
- [x] 7. Run validation and update this Logics chain with evidence before closeout.

# Acceptance criteria
- AC1: H1 is fixed and tested: a slow CSV/wide export stream no longer blocks a concurrent DuckDB-backed request.
- AC2: S1 is fixed and tested: DBC parse/import errors expose sanitized messages without local path disclosure.
- AC3: S3 is fixed and tested: multi-file uploads enforce an aggregate request budget.
- AC4: M1/M2 are fixed and tested: decimation uses bound parameters and no-match signal filters produce stable empty results.
- AC5: S2/S4/S5 are resolved consistently across implementation, CLI/docs and tests.
- AC6: Low-risk cleanup findings are either implemented or deferred with explicit rationale in the final report.
- AC7: Final validation evidence is recorded with commands and outcomes.

# AC Traceability
- request-AC1 -> This task. Proof: H1 implemented in `TraceStore.iter_export_batches` and `Session.borrow_store`; `test_export_batches_release_store_lock_while_consumed` proves the store lock is available while exported batches are still consumed.
- request-AC2 -> This task. Proof: S1 implemented with sanitized DBC/import failure details; `test_invalid_dbc_error_does_not_leak_paths` and `test_import_failure_job_does_not_leak_paths` cover API and job details.
- request-AC3 -> This task. Proof: S3 implemented with aggregate upload accounting in `_spool`; `test_spool_enforces_aggregate_upload_limit` covers multi-file aggregate overflow.
- request-AC4 -> This task. Proof: M1/M2 implemented in `_decimate` and `_frame_filters`; `test_signal_series_degenerate_timestamps_do_not_generate_bad_sql` and `test_trace_signal_filter_without_catalog_match_returns_no_rows` cover the regressions.
- request-AC5 -> This task. Proof: S2/S4/S5 decisions are implemented in `cli.py`, `security.py`, and `README.md`; `test_missing_host_is_rejected` covers missing Host rejection.
- request-AC6 -> This task. Proof: Low-risk cleanups completed for `series_cache`, ASC DLC 0, duplicate `_f`, and streaming helper; `iter_asc` and exact timestamp tolerance are deferred in the report with rationale.
- request-AC7 -> This task. Proof: Validation evidence records `.venv/bin/ruff check .` and `.venv/bin/pytest` passing on 2026-07-23.

# Validation
- Run `ruff check .`.
- Run `pytest` or the targeted subset covering export streaming, security errors, upload limits, decimation, trace filters and ASC parsing; justify any skipped broader suite.
- Run `logics-manager lint --require-status`.
- Run `logics-manager audit --group-by-doc`.
- Use `logics-manager flow progress task logics/tasks/task_030_repondre_a_l_audit_code_du_23_juillet_2026.md --progress <n>%` during multi-wave work.
- Run `logics-manager flow finish task logics/tasks/task_030_repondre_a_l_audit_code_du_23_juillet_2026.md` after implementation and validation.
- PASSED 2026-07-23: `.venv/bin/ruff check .` -> All checks passed.
- PASSED 2026-07-23: `.venv/bin/pytest tests/test_api.py tests/test_export.py tests/test_security.py` -> 59 passed, 1 warning.
- PASSED 2026-07-23: `.venv/bin/pytest` -> 155 passed, 1 warning.
- .venv/bin/ruff check . passed; .venv/bin/pytest passed with 155 passed, 1 warning; targeted API/export/security suite passed with 59 passed, 1 warning.
- Finish workflow executed on 2026-07-23.
- Linked backlog/request close verification passed.

# Report
- Implementation complete.
- H1: `TraceStore.iter_export_batches` drains DuckDB Arrow batches under the connection lock and yields them after release; `api_export` now borrows the store through a public session helper.
- S1: DBC and import failures return sanitized API/job details without local paths.
- S3: upload spooling enforces one aggregate request budget for trace plus DBC uploads.
- M1/M2: `_decimate` uses bound timestamp/span params and avoids non-finite decimation; no-match signal filters now return zero frames deterministically.
- S2/S4/S5: LAN keeps token URL compatibility for stock browsers, but disables access logs and uses warning-level Uvicorn logs; README documents server-side import as arbitrary local file read by design and the LAN disablement; missing `Host` is rejected.
- Low-risk cleanup: `series_cache` is purged on sample replacement, ASC DLC 0 numeric metadata is covered, duplicate `_f` is removed, and `iter_asc` plus exact frame timestamp tolerance are deferred because they are either public surface or require a UI/API contract change.
- Finished on 2026-07-23.
- Linked backlog item(s): `item_029_repondre_a_l_audit_code_du_23_juillet_2026`
- Related request(s): `req_014_repondre_a_l_audit_code_du_23_juillet_2026`

# AI Context
- Summary: Implement the response to `docs/audit-code-2026-07-23.md`.
- Keywords: audit-code-2026-07-23, duckdb-lock, StreamingResponse, sanitized-errors, aggregate-upload, decimation, trace-filter
- Use when: Executing the post-audit code hardening chain.
- Skip when: Work belongs to PWA static hosting or unrelated feature delivery.

# Links
- Request: `req_014_repondre_a_l_audit_code_du_23_juillet_2026`
- Product brief(s): (none yet)
- Architecture decision(s): (none yet)
