## task_021_improve_accessibility_and_minimal_responsive_support - Improve accessibility and minimal responsive support
> From version: 0.1.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: Medium
> Theme: Implementation delivery
> Reminder: Update status/understanding/confidence/progress and linked request/backlog references when you edit this doc.
> Non-semantic edit: task-level AC traceability closure (req_007 AC17).

# Definition of Done (DoD)
- [x] The backlog scope is implemented.
- [x] Acceptance criteria are covered.
- [x] Validation passes.
- [x] Implementation, tests and documentation are delivered together in one dedicated commit for this task.

# Delivery order and commit boundary
- Sequence: 5 of 7; start after task 020 is complete.
- Commit only AC13-AC14 and their E2E coverage; preserve the current visual hierarchy.
- Suggested commit: `fix(ui): improve accessibility and responsive reachability`.

# Backlog
- `item_021_improve_accessibility_and_minimal_responsive_support`

# Acceptance criteria
- AC13: Les favoris, filtres, onglets, lignes de table, dialogues et redimensionneurs
- AC14: Aucun controle principal ne deborde a 1024x768, 1280x720 et 1600x900. A

# Validation
- Run accessibility checks and E2E at 390x844, 1024x768, 1280x720 and 1600x900.
- Verify CI fails when Chromium cannot launch, then run the full suite and lint.
- Run `python3 -m logics_manager lint --require-status`.
- Use `python3 -m logics_manager flow progress task task_021_improve_accessibility_and_minimal_responsive_support.md --progress <n>%` during multi-wave work.
- Run `python3 -m logics_manager flow finish task task_021_improve_accessibility_and_minimal_responsive_support.md` after implementation.
- Finish workflow executed on 2026-07-18.
- Linked backlog/request close verification passed.

# Report
- Implementation complete.
- AC13 — Accessibility + Pointer Events: favorite stars (`role=button`, `aria-pressed`,
- Finished on 2026-07-18.
- Linked backlog item(s): `item_021_improve_accessibility_and_minimal_responsive_support`
- Related request(s): `req_007_finaliser_workflow_diagnostic_et_clarifier_cantracediag`
  Enter/Space), filters (`aria-label`), table rows (`tabindex`, `role=button`, Enter/Space
  select), and side/vertical resizers (`role=separator`, `aria-orientation`, arrow-key
  resize) are named and keyboard-operable (`web/index.html`, `web/app.js`). Graph pan/zoom/
  cursor drag and all resizers now use Pointer Events with `setPointerCapture` and
  `touch-action: none`, with no mouse regression. Automated accessibility coverage runs in
  Playwright: `tests/test_e2e_ui.py::test_main_controls_have_accessible_names`,
  `::test_favorite_toggles_via_keyboard`, `::test_trace_dialogs_close_with_escape`.
- AC14 — Responsive + hard-fail E2E: `min-width: 0` down the centre flex column lets the
  plotbar wrap and inner areas scroll, so no main control overflows. A parametrized E2E
  runs all four mandated viewports —
  `tests/test_e2e_ui.py::test_no_horizontal_overflow_at_supported_viewports[1024-768|1280-720|1600-900|390-844]`
  — and `::test_narrow_viewport_keeps_critical_actions_reachable` checks import/load/
  filter/export/report stay reachable at 390×844. The `browser` fixture now fails (not
  skips) when Chromium cannot launch under `CI`, and the CI workflow installs
  `playwright chromium` and runs pytest with `CI=true` (`.github/workflows/ci.yml`).
- Note on tabs: AC13/AC14 mention tab controls; the Analysis/Trace/Report tabs are built in
  task_023 (AC4) and inherit these accessibility patterns and viewport coverage there.
- Validation: `ruff check .` clean; full suite `133 passed, 0 skipped` with Chromium
  installed (E2E executed, not skipped) in an isolated `uv` environment.

# AI Context
- Summary: Implement improve accessibility and minimal responsive support.
- Keywords: task, implementation, backlog, runtime, python
- Use when: You need a bounded implementation task for a backlog item.
- Skip when: The work is still at the request or backlog shaping stage.

# Links
- Request: `req_007_finaliser_workflow_diagnostic_et_clarifier_cantracediag`
- Product brief(s): (none yet)
- Architecture decision(s): (none yet)

# AC Traceability
- request-AC13 -> task_021. Proof: named keyboard-operable controls + Pointer Events; tests/test_e2e_ui.py::test_main_controls_have_accessible_names, ::test_favorite_toggles_via_keyboard, ::test_trace_dialogs_close_with_escape.
- request-AC14 -> task_021. Proof: no horizontal overflow across 1024x768/1280x720/1600x900 and minimal 390x844, CI hard-fails without Chromium; tests/test_e2e_ui.py::test_no_horizontal_overflow_at_supported_viewports, ::test_narrow_viewport_keeps_critical_actions_reachable.
