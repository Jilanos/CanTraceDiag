## task_022_modularize_frontend_and_align_dependencies_ci_and_docs - Modularize frontend and align dependencies CI and docs
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
- Sequence: 6 of 7; start after task 021 is complete.
- Commit AC15-AC17 while preserving the existing UI hierarchy for task 023.
- Suggested commit: `refactor(web): modularize workspace foundations`.

# Backlog
- `item_022_modularize_frontend_and_align_dependencies_ci_and_docs`

# Acceptance criteria
- AC15: `app.js` et le CSS embarque sont decoupes par domaines `core`, `import`,
- AC16: `pyarrow` est utilise par l'export Parquet ou retire ; `python-can` est retire
- AC17: Le README, la roadmap, le backlog produit et les documents Logics ne

# Validation
- Run module loading/E2E surface checks, dependency checks and CI performance budgets.
- Run the complete Python and browser suites plus `ruff check .`.
- Run `python3 -m logics_manager lint --require-status`.
- Use `python3 -m logics_manager flow progress task task_022_modularize_frontend_and_align_dependencies_ci_and_docs.md --progress <n>%` during multi-wave work.
- Run `python3 -m logics_manager flow finish task task_022_modularize_frontend_and_align_dependencies_ci_and_docs.md` after implementation.
- Finish workflow executed on 2026-07-18.
- Linked backlog/request close verification passed.

# Report
- Implementation complete.
- AC15 — Frontend modularization: the 1517-line `web/app.js` is split into framework-free
- Finished on 2026-07-18.
- Linked backlog item(s): `item_022_modularize_frontend_and_align_dependencies_ci_and_docs`
- Related request(s): `req_007_finaliser_workflow_diagnostic_et_clarifier_cantracediag`
  domain scripts under `web/js/` (`core`, `import`, `signals`, `plot`, `report`, `trace`,
  `inspector`, `main`) loaded in order (core first, main last) so shared state/utilities
  resolve before use; the embedded CSS is extracted to `web/styles.css` and linked. `main.js`
  exposes an explicit `window.__ctd` surface (state + curated actions) and the Playwright
  suite drives the app through it instead of internal globals. The token `<meta>` injection
  and CSP (`script-src 'self'`) still hold. Validated by the full E2E suite executing the
  real modular UI in Chromium (18 tests: plot/cursors/trace/dialogs/viewports/a11y).
- AC16 — Dependencies and dead code: `python-can` (declared, unused) removed from
  `pyproject.toml`; `pyarrow` retained (used by the Parquet export); dead `TraceStore.
  _window_clause` removed and the duplicated `_id_hex` helper de-duplicated (api imports it
  from store). A synthetic time/memory budget guards the hot paths
  (`tests/test_perf_budget.py`: bounded page-query memory, point-bounded series, hot-query
  time ceiling), and CI runs the whole suite on Python 3.11 and 3.12.
- Packaging: `package-data` now ships `web/js/*.js` and `web/*.css`; CI installs Playwright
  Chromium and runs with `CI=true`.
- Validation: `ruff check .` clean; full suite `136 passed, 0 skipped` with Chromium
  (E2E executed) in an isolated `uv` environment.

# AI Context
- Summary: Implement modularize frontend and align dependencies ci and docs.
- Keywords: task, implementation, backlog, runtime, python
- Use when: You need a bounded implementation task for a backlog item.
- Skip when: The work is still at the request or backlog shaping stage.

# Links
- Request: `req_007_finaliser_workflow_diagnostic_et_clarifier_cantracediag`
- Product brief(s): (none yet)
- Architecture decision(s): (none yet)
