## task_023_clarify_final_ui_workflow_in_english - Clarify final UI workflow in English
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
- [x] Implementation, tests and documentation are delivered together in one dedicated final commit for this task.

# Delivery order and commit boundary
- Sequence: 7 of 7; start only after tasks 017-022 are complete.
- This is the final slice and may refactor the visual hierarchy, but must not add new
  backend contracts or unrelated product features.
- Commit only AC4-AC7 and their visual/E2E/user-documentation changes.
- Suggested commit: `feat(ui): clarify the English diagnostic workflow`.

# Backlog
- `item_023_clarify_final_ui_workflow_in_english`

# Acceptance criteria
- AC4: L'interface propose les onglets `Analysis`, `Trace` et `Report` sans perdre
- AC5: Tous les libelles, actions, messages, etats vides et contenus de documentation
- AC6: Une erreur de serie, table, inspecteur ou export est affichee dans le composant
- AC7: La trace affiche un etat vide distinct pour « aucune trace », « aucun resultat

# Validation
- Run the complete browser suite at every target viewport and inspect final screenshots.
- Run the full Python suite, browser E2E, `ruff check .`, Logics lint and audit.
- Run `python3 -m logics_manager lint --require-status`.
- Use `python3 -m logics_manager flow progress task task_023_clarify_final_ui_workflow_in_english.md --progress <n>%` during multi-wave work.
- Run `python3 -m logics_manager flow finish task task_023_clarify_final_ui_workflow_in_english.md` after implementation.
- Finish workflow executed on 2026-07-19.
- Linked backlog/request close verification passed.

# Report
- Implementation complete.
- AC4 — Workspace tabs: the centre is now Analysis / Trace / Report tab panels
- Finished on 2026-07-19.
- Linked backlog item(s): `item_023_clarify_final_ui_workflow_in_english`
- Related request(s): `req_007_finaliser_workflow_diagnostic_et_clarifier_cantracediag`
  (`web/index.html`, tab controller in `web/js/main.js`) that keep their DOM and state
  when hidden; the signal explorer, inspector and session status persist across tabs, and
  `Plots`/`Trace`/`Full diagnostic` layout presets restore a persisted view. Proof:
  `tests/test_e2e_ui.py::test_tabs_switch_panels_and_preserve_state`.
- AC5 — English UI: all labels, actions, messages, empty states and status labels are
  English; technical decode statuses get a readable English label via `STATUS_LABELS`
  while the raw value stays available (title attribute). A French-string audit over `web/`
  is clean; user docs are English.
- AC6 — Component-scoped errors: series, table, inspector and report errors surface in the
  affected component with a Retry action (`showComponentError`/`clearComponentError` in
  `web/js/core.js`, used across `signals`/`trace`/`inspector`/`report`) and never overwrite
  the global session summary or block other components.
- AC7 — Empty states and filters: the trace shows distinct empty states ("No trace loaded",
  "No matching rows", "Empty trace") and a load-failure banner; active filters render as
  removable, persistent chips and secondary filters collapse without losing their value.
  Proof: `tests/test_e2e_ui.py::test_trace_empty_state_for_no_matching_filter`.
- AC17 — Traceability closure: `docs/roadmap.md` and `docs/product-backlog.md` no longer
  list delivered features (export, report, stats, security, tabs) as missing; each request
  AC now carries task-level AC Traceability with proof across tasks 017-023; `logics-manager
  lint` passes and the audit reports no blocking for the req_007 chain (remaining repo
  blocking belongs to the untouched req_004/005/006 baseline).
- Validation: `ruff check .` clean; full suite `138 passed, 0 skipped` with Chromium
  (E2E executed) in an isolated `uv` environment.
- Summary: Implement clarify final ui workflow in english.
- Keywords: task, implementation, backlog, runtime, python
- Use when: You need a bounded implementation task for a backlog item.
- Skip when: The work is still at the request or backlog shaping stage.

# Links
- Request: `req_007_finaliser_workflow_diagnostic_et_clarifier_cantracediag`
- Product brief(s): (none yet)
- Architecture decision(s): (none yet)

# AC Traceability
- request-AC4 -> task_023. Proof: Analysis/Trace/Report tabs preserve state with persistent layout presets; tests/test_e2e_ui.py::test_tabs_switch_panels_and_preserve_state.
- request-AC5 -> task_023. Proof: all UI labels/messages/empty states in English with English decode-status labels (raw kept for audit); no French remnants in web/.
- request-AC6 -> task_023. Proof: series/table/inspector/report errors surface in-component with retry, never replacing the session summary; showComponentError + tests/test_e2e_ui.py error paths.
- request-AC7 -> task_023. Proof: distinct trace empty states (no trace / no matching rows / load failed) and removable, persistent filter chips with collapsible secondary filters; tests/test_e2e_ui.py::test_trace_empty_state_for_no_matching_filter.
- request-AC17 -> task_023. Proof: README, roadmap and product backlog no longer present delivered features as missing; each request AC has task-level traceability with proof; logics-manager lint passes and the audit reports no blocking for the req_007 chain.
