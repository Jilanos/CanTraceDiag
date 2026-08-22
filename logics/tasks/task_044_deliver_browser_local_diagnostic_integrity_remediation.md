## task_044_deliver_browser_local_diagnostic_integrity_remediation - Deliver browser-local diagnostic integrity remediation
> From version: 1.0.0
> Schema version: 1.0
> Status: In progress
> Understanding: 90%
> Confidence: 85%
> Progress: 60%
> Complexity: Medium
> Theme: Implementation delivery
> Reminder: Update status/understanding/confidence/progress and linked request/backlog references when you edit this doc.
> Indicators reviewed: 2026-08-22 12:25:36
> Owner: codex

# AI Context
- Summary: Orchestrate the two PWA integrity slices from failing regressions through validated patch release evidence.
- Keywords: deliver, browser, local, diagnostic, integrity, remediation
- Use when: Delivering or closing the linked anomaly-count and DBC-identity backlog items as one release chain.
- Skip when: Implementing unrelated PWA migration milestones or changing the Python reference contract.

# Context
- Start from the two deterministic reproductions linked through the parent remediation request.
- Deliver exact anomaly counts first because it is the smaller isolated contract, then change DBC identity with explicit legacy-entry compatibility.
- Keep the two backlog slices independently testable while closing and releasing them through this shared orchestration task.

# Plan
- [ ] 1. Capture failing regression tests for repeated anomaly counts and for the deterministic legacy DBC digest collision before changing implementation behavior.
- [ ] 2. Separate unique event-type discovery from exact event counting, align the local report payload with the Python reference, and verify backend plus rendered-report behavior.
- [ ] 3. Introduce collision-safe DBC content identity and a bounded compatibility path for existing valid browser-local library entries without claiming recovery of already-overwritten content.
- [ ] 4. Run focused tests after each slice, then run the complete Node PWA suite, static build, Chromium browser smoke, Ruff, Python suite, Logics lint, and Logics audit.
- [ ] 5. Close each backlog slice with acceptance-criteria evidence, then follow the mandatory patch-release sequence and record commit, CI, tag, and release proof before final closeout.
- [ ] ADR 009 checkpoint: update affected Logics docs during each meaningful wave and leave the repo commit-ready.
- [ ] Keep commit creation under operator control; do not force one commit per micro-step.
- [ ] GATE: do not close until lint, audit, and scaffold validation pass.

# Backlog
- `item_047_preserve_exact_anomaly_counts_in_browser_local_reports`
- `item_048_adopt_collision_safe_browser_local_dbc_content_identity`

# Definition of Done (DoD)
- [ ] Generated request, product, backlog, and task docs are present.
- [ ] Context-pack handoff is available when requested.
- [ ] Validation passes.
- [ ] Meaningful waves followed ADR 009: affected docs updated and the repo left commit-ready without automatic commits.

# AC Traceability
- request-AC1 -> `item_047_preserve_exact_anomaly_counts_in_browser_local_reports`. Proof deferred to slice closeout.
- request-AC2 -> `item_047_preserve_exact_anomaly_counts_in_browser_local_reports`. Proof deferred to slice closeout.
- request-AC5 -> `item_047_preserve_exact_anomaly_counts_in_browser_local_reports`. Proof deferred to slice closeout.
- request-AC6 -> `item_047_preserve_exact_anomaly_counts_in_browser_local_reports`. Proof deferred to slice closeout.
- request-AC3 -> `item_048_adopt_collision_safe_browser_local_dbc_content_identity`. Proof deferred to slice closeout.
- request-AC4 -> `item_048_adopt_collision_safe_browser_local_dbc_content_identity`. Proof deferred to slice closeout.
- request-AC5 -> `item_048_adopt_collision_safe_browser_local_dbc_content_identity`. Proof deferred to slice closeout.
- request-AC6 -> `item_048_adopt_collision_safe_browser_local_dbc_content_identity`. Proof deferred to slice closeout.

# Validation
- (no validation recorded yet)

# Report
- Not started.

# Links
- Request: `req_026_restore_browser_local_diagnostic_data_integrity`
- Product brief(s): `prod_012_trustworthy_browser_local_diagnostics`
- Architecture decision(s): (none yet)
