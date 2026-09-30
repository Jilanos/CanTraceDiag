## task_047_deliver_opt_in_signal_integral_analysis_and_remembered_dbc_loading - Deliver opt-in signal integral analysis and remembered DBC loading
> From version: 1.0.0
> Schema version: 1.0
> Status: Ready
> Understanding: 90%
> Confidence: 85%
> Progress: 0%
> Complexity: Medium
> Theme: Implementation delivery
> Reminder: Update status/understanding/confidence/progress and linked request/backlog references when you edit this doc.
> Indicators reviewed: 2026-09-30 12:26:46

# AI Context
Deliver remembered DBC defaults independently, then the integral engine and its dependent opt-in UI. Keep implementation proof per request AC and follow the repository release policy for functional delivery.

# Priority
Medium — Requested diagnostic and repeated-load improvements follow existing High priority correctness work.

# Context
- Existing cursor statistics stay available; integral results require explicit opt-in. DBC selection history must survive browser reload without overwriting manual choices.

# Plan
- [ ] 1. Confirm canonical module locations and baseline cursor/import tests; retain this corpus scope during any ongoing PWA relocation.
- [ ] 2. Implement the independent remembered-DBC slice, migrate history safely, and verify reload/restart plus manual deselection behavior.
- [ ] 3. Implement and validate the shared trapezoidal integral contract in full-resolution local and server stores and adapters.
- [ ] 4. Build the opt-in per-signal UI after the numeric contract; verify disabled mode causes no integral requests/computation and protect against stale results.
- [ ] 5. Run focused numerical parity, storage lifecycle, and browser regression suites; record per-AC evidence and update affected Logics documents at meaningful checkpoints.
- [ ] 6. For functional release delivery follow the repository policy: validate locally, implementation commit, prepare and commit next SemVer version, push, wait for CI on that exact preparation SHA, push an annotated version tag, verify tag-triggered release, and record SHA/CI/tag/release evidence before closeout.
- [ ] ADR 009 checkpoint: update affected Logics docs during each meaningful wave and leave the repo commit-ready.
- [ ] Keep commit creation under operator control; do not force one commit per micro-step.
- [ ] GATE: do not close until lint, audit, and scaffold validation pass.

# Backlog
- `item_054_compute_exact_range_numeric_signal_integrals_in_local_and_server_stores`
- `item_055_expose_per_signal_cursor_integral_analysis_only_after_explicit_activation`
- `item_056_persist_and_preselect_the_exact_last_successful_dbc_load_set`

# Definition of Done (DoD)
- [ ] All three backlog slices meet their acceptance criteria in the PWA and supported server UI.
- [ ] Numeric fixtures establish integral accuracy and parity independently of zoom/downsampling.
- [ ] Browser tests prove opt-in-only computation and restart-persistent DBC defaults with preserved manual choices.
- [ ] Regression checks preserve cursor dragging, range statistics, and trace import/conflict handling.
- [ ] Request AC1 through AC6 have concrete validation evidence before closeout.
- [ ] Logics lint, audit, and scoped validation pass.
- [ ] Functional release evidence includes implementation/version SHAs, CI, annotated tag, and release outcome.

# AC Traceability
- request-AC3 -> `item_054_compute_exact_range_numeric_signal_integrals_in_local_and_server_stores`. Proof deferred to slice closeout.
- request-AC6 -> `item_054_compute_exact_range_numeric_signal_integrals_in_local_and_server_stores`. Proof deferred to slice closeout.
- request-AC1 -> `item_055_expose_per_signal_cursor_integral_analysis_only_after_explicit_activation`. Proof deferred to slice closeout.
- request-AC2 -> `item_055_expose_per_signal_cursor_integral_analysis_only_after_explicit_activation`. Proof deferred to slice closeout.
- request-AC6 -> `item_055_expose_per_signal_cursor_integral_analysis_only_after_explicit_activation`. Proof deferred to slice closeout.
- request-AC4 -> `item_056_persist_and_preselect_the_exact_last_successful_dbc_load_set`. Proof deferred to slice closeout.
- request-AC5 -> `item_056_persist_and_preselect_the_exact_last_successful_dbc_load_set`. Proof deferred to slice closeout.
- request-AC6 -> `item_056_persist_and_preselect_the_exact_last_successful_dbc_load_set`. Proof deferred to slice closeout.

# Validation
- (no validation recorded yet)

# Report
- Not started.

# Links
- Request: `req_032_add_opt_in_cursor_integral_analysis_and_restore_the_last_loaded_dbc_selection`
- Product brief(s): `prod_015_optional_cursor_integration_and_reusable_dbc_import_defaults`
- Architecture decision(s): (none yet)
