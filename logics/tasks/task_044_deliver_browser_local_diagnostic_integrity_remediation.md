## task_044_deliver_browser_local_diagnostic_integrity_remediation - Deliver browser-local diagnostic integrity remediation
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: Medium
> Theme: Implementation delivery
> Reminder: Update status/understanding/confidence/progress and linked request/backlog references when you edit this doc.
> Indicators reviewed: 2026-08-22 12:37:57
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
- [x] 1. Capture failing regression tests for repeated anomaly counts and for the deterministic legacy DBC digest collision before changing implementation behavior.
- [x] 2. Separate unique event-type discovery from exact event counting, align the local report payload with the Python reference, and verify backend plus rendered-report behavior.
- [x] 3. Introduce collision-safe DBC content identity and a bounded compatibility path for existing valid browser-local library entries without claiming recovery of already-overwritten content.
- [x] 4. Run focused tests after each slice, then run the complete Node PWA suite, static build, Chromium browser smoke, Ruff, Python suite, Logics lint, and Logics audit.
- [x] 5. Close each backlog slice with acceptance-criteria evidence, then follow the mandatory patch-release sequence and record commit, CI, tag, and release proof before final closeout.
- [x] ADR 009 checkpoint: update affected Logics docs during each meaningful wave and leave the repo commit-ready.
- [x] Keep commit creation under operator control; do not force one commit per micro-step.
- [x] GATE: do not close until lint, audit, and scaffold validation pass.

# Backlog
- `item_047_preserve_exact_anomaly_counts_in_browser_local_reports`
- `item_048_adopt_collision_safe_browser_local_dbc_content_identity`

# Definition of Done (DoD)
- [x] Generated request, product, backlog, and task docs are present.
- [x] Context-pack handoff is available when requested.
- [x] Validation passes.
- [x] Meaningful waves followed ADR 009: affected docs updated and the repo left commit-ready without automatic commits.

# AC Traceability
- request-AC1 -> This task. Proof: `e3d5b55` adds exact local event-type counts; Node regression and Chromium repeated-event smoke show `ErrorFrame×2` and `Status×1`.
- request-AC2 -> This task. Proof: Chromium repeated-event smoke renders the backend counts without recomputation.
- request-AC3 -> This task. Proof: `e3d5b55` replaces the collision-prone identifier with SHA-256; Node collision and identical-content tests pass.
- request-AC4 -> This task. Proof: Node migration and reuse test preserves a usable legacy library entry under its new SHA-256 identifier.
- request-AC5 -> This task. Proof: Ruff, pytest (166 passed), Node PWA tests (27 passed), standard and repeated-event Chromium smokes, Docker smoke, and CI run 32567940350 passed.
- request-AC6 -> This task. Proof: version 1.0.18 was prepared, pushed, tagged, and released by successful workflow 32568014322.

# Validation
- (no validation recorded yet)
- command: `.venv/bin/ruff check . && .venv/bin/pytest && node --experimental-strip-types --test spikes/pwa-local-engine/tests/*.test.ts && node spikes/pwa-local-engine/build-browser.mjs` | result: passed | date: 2026-08-22 | note: Ruff passed; pytest 166 passed; Node PWA tests 27 passed; standard and repeated-event Chromium smokes, Docker smoke, CI 32567940350, and release workflow 32568014322 passed for v1.0.18.
- Finish workflow executed on 2026-08-22.
- Linked backlog/request close verification passed.

# Report
- Not started.
- Finished on 2026-08-22.
- Linked backlog item(s): `item_047_preserve_exact_anomaly_counts_in_browser_local_reports`, `item_048_adopt_collision_safe_browser_local_dbc_content_identity`
- Related request(s): `req_026_restore_browser_local_diagnostic_data_integrity`

# Links
- Request: `req_026_restore_browser_local_diagnostic_data_integrity`
- Product brief(s): `prod_012_trustworthy_browser_local_diagnostics`
- Architecture decision(s): (none yet)
