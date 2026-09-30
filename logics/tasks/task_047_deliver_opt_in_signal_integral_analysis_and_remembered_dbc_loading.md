## task_047_deliver_opt_in_signal_integral_analysis_and_remembered_dbc_loading - Deliver opt-in signal integral analysis and remembered DBC loading
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 95%
> Confidence: 90%
> Progress: 100%
> Complexity: Medium
> Theme: Implementation delivery
> Reminder: Update status/understanding/confidence/progress and linked request/backlog references when you edit this doc.
> Indicators reviewed: 2026-09-30 13:57:06
> Owner: Claude

# AI Context
Deliver remembered DBC defaults independently, then the integral engine and its dependent opt-in UI. Keep implementation proof per request AC and follow the repository release policy for functional delivery.

# Priority
Medium — Requested diagnostic and repeated-load improvements follow existing High priority correctness work.

# Context
- Existing cursor statistics stay available; integral results require explicit opt-in. DBC selection history must survive browser reload without overwriting manual choices.

# Plan
- [x] 1. Confirm canonical module locations and baseline cursor/import tests; retain this corpus scope during any ongoing PWA relocation.
- [x] 2. Implement the independent remembered-DBC slice, migrate history safely, and verify reload/restart plus manual deselection behavior.
- [x] 3. Implement and validate the shared trapezoidal integral contract in full-resolution local and server stores and adapters.
- [x] 4. Build the opt-in per-signal UI after the numeric contract; verify disabled mode causes no integral requests/computation and protect against stale results.
- [x] 5. Run focused numerical parity, storage lifecycle, and browser regression suites; record per-AC evidence and update affected Logics documents at meaningful checkpoints.
- [x] 6. For functional release delivery follow the repository policy: validate locally, implementation commit, prepare and commit next SemVer version, push, wait for CI on that exact preparation SHA, push an annotated version tag, verify tag-triggered release, and record SHA/CI/tag/release evidence before closeout.
- [x] ADR 009 checkpoint: update affected Logics docs during each meaningful wave and leave the repo commit-ready.
- [x] Keep commit creation under operator control; do not force one commit per micro-step.
- [x] GATE: do not close until lint, audit, and scaffold validation pass.

# Backlog
- `item_054_compute_exact_range_numeric_signal_integrals_in_local_and_server_stores`
- `item_055_expose_per_signal_cursor_integral_analysis_only_after_explicit_activation`
- `item_056_persist_and_preselect_the_exact_last_successful_dbc_load_set`

# Definition of Done (DoD)
- [x] All three backlog slices meet their acceptance criteria in the PWA and supported server UI.
- [x] Numeric fixtures establish integral accuracy and parity independently of zoom/downsampling.
- [x] Browser tests prove opt-in-only computation and restart-persistent DBC defaults with preserved manual choices.
- [x] Regression checks preserve cursor dragging, range statistics, and trace import/conflict handling.
- [x] Request AC1 through AC6 have concrete validation evidence before closeout.
- [x] Logics lint, audit, and scoped validation pass.
- [x] Functional release evidence includes implementation/version SHAs, CI, annotated tag, and release outcome.

# AC Traceability
- request-AC1 -> This task. Proof: implemented in d03b57c (`src/cantracediag/web/js/integral.js`, `#integralBtn`); `tests/test_e2e_ui.py::test_integral_is_absent_and_request_free_until_enabled` asserts no panel, no integral column and zero `/api/signal-integral` requests with both cursors placed, and `test_last_dbc_set_is_prechecked_after_reload_and_server_restart` asserts it stays off on a newly imported trace; the PWA smoke (24f2563) asserts `requests: 0` by default.
- request-AC2 -> This task. Proof: `test_integral_enable_follow_target_and_cursors_then_disable`, `test_integral_is_keyboard_operable`, `test_integral_rejects_stale_responses` and `test_removing_the_target_or_reloading_disables_integral` cover enable, target switch, cursor drag, missing-cursor reason, disable, stale responses and keyboard operation while range statistics keep rendering; the PWA smoke shows `73.387 rpm·s` with the trapezoidal method label.
- request-AC3 -> This task. Proof: implemented in 2ae012f (`src/cantracediag/integral.py`, `spikes/pwa-local-engine/src/integral.ts`); the shared `tests/fixtures/integral_cases.json` (constant 2 on [1,4] = 6, ramp on [0.5,2.5] = 3, -2..2 = 0, reversed/equal cursors, irregular spacing, duplicates, interpolated and missing boundaries, non-finite and text samples) passes in `tests/test_integral.py` (pure engine, DuckDB store, API) and `spikes/pwa-local-engine/tests/integral.test.ts` (pure engine and LocalTraceStore), plus decimation/zoom invariance tests.
- request-AC4 -> This task. Proof: implemented in b7c3f47 and d03b57c; `tests/test_workspace.py::test_mixed_uploaded_and_reused_set_survives_restart` (ordered uploaded+reused digests after a server restart and trace-only reuse), the adapter test `persists the ordered mixed uploaded/reused set and survives a new adapter (reload)`, the PWA smoke (prechecked `1 DBC (1 from library)` after reload, then a trace-only load) and `test_last_dbc_set_is_prechecked_after_reload_and_server_restart` (2 DBCs prechecked after reload and after a server restart, then trace-only load).
- request-AC5 -> This task. Proof: the same E2E test and the PWA smoke keep a manual uncheck-all across library reopen and a background `loadLibrary()` refresh; `test_same_name_different_content_stays_distinct`, `test_failed_and_unresolved_imports_keep_previous_history`, `test_malformed_history_and_purge_degrade_to_empty` and the adapter tests for identical content, failed/unresolved imports, deleted entries, unique-only legacy name migration, malformed history, purge and storage failure cover the persistence contract.
- request-AC6 -> This task. Proof: full validation passed on 2026-09-30 with `.venv/bin/ruff check . && .venv/bin/python -m pytest && node --experimental-strip-types --test spikes/pwa-local-engine/tests/*.test.ts && node spikes/pwa-local-engine/build-browser.mjs && node spikes/pwa-local-engine/browser-smoke.mjs` (ruff clean, 246 pytest incl. 33 Playwright E2E, 82 node tests, build, PWA smoke `ok: true`), covering zero integral work while disabled and unchanged cursor dragging, range statistics and import/conflict flows.

# Validation
- command: `.venv/bin/ruff check . && .venv/bin/python -m pytest && node --experimental-strip-types --test spikes/pwa-local-engine/tests/*.test.ts && node spikes/pwa-local-engine/build-browser.mjs && node spikes/pwa-local-engine/browser-smoke.mjs` | result: passed | date: 2026-09-30 | note: ruff clean; 246 pytest passed (incl. 33 Playwright E2E); 82 node tests passed; build ok; browser smoke ok with integral and remembered-DBC scenarios.
- command: `.venv/bin/ruff check . && .venv/bin/python -m pytest && node --experimental-strip-types --test spikes/pwa-local-engine/tests/*.test.ts && node spikes/pwa-local-engine/build-browser.mjs && node spikes/pwa-local-engine/browser-smoke.mjs` | result: passed | date: 2026-09-30 | note: v1.2.0 at 6f383b8: 246 pytest, 82 node, build and smoke ok; CI 36711072008 and release 36711354122 succeeded
- Finish workflow executed on 2026-09-30.
- Linked backlog/request close verification passed.

# Report
- Wave 1 (2ae012f): shared signed trapezoidal integral contract in `src/cantracediag/integral.py` and `spikes/pwa-local-engine/src/integral.ts`, `TraceStore.signal_integral` (bounded DuckDB query, rowid-stable duplicates), `LocalTraceStore.signalIntegral`, `GET /api/signal-integral` on the server (decodes only the target signal widened to the bracketing samples) and in the PWA adapter.
- Wave 2 (b7c3f47): last successful DBC set persisted by content digest — server via the last-analysis manifest (`Workspace.last_dbc_digests`, `last_session_digests` on `/api/dbc-library`), PWA via `ctd.pwa.last-dbc-selection.v1`, committed only after completion/resolution, cleared on purge.
- Wave 3 (d03b57c): opt-in `∫ Integral` UI (`web/js/integral.js`) and one-shot picker defaulting in `web/js/import.js` that preserves manual edits including uncheck-all.
- Wave 4 (24f2563, 2f10e89): PWA browser smoke scenarios and README documentation. The smoke now launches Chromium with `--password-store=basic --use-mock-keychain`: on this WSL host Chromium otherwise blocked on the desktop keyring and never committed its first navigation (the pre-task baseline hung the same way).
- Release (operator-approved): implementation commits 2ae012f..38ed181, version preparation 6f383b8 (v1.2.0) pushed to main; CI run 36711072008 passed on that SHA; annotated tag v1.2.0 -> 6f383b8; release workflow 36711354122 succeeded and published https://github.com/Jilanos/CanTraceDiag/releases/tag/v1.2.0; evidence recorded in `logics/release/evidence.jsonl`.
- Finished on 2026-09-30.
- Linked backlog item(s): `item_054_compute_exact_range_numeric_signal_integrals_in_local_and_server_stores`, `item_055_expose_per_signal_cursor_integral_analysis_only_after_explicit_activation`, `item_056_persist_and_preselect_the_exact_last_successful_dbc_load_set`
- Related request(s): `req_032_add_opt_in_cursor_integral_analysis_and_restore_the_last_loaded_dbc_selection`

# Links
- Request: `req_032_add_opt_in_cursor_integral_analysis_and_restore_the_last_loaded_dbc_selection`
- Product brief(s): `prod_015_optional_cursor_integration_and_reusable_dbc_import_defaults`
- Architecture decision(s): (none yet)
