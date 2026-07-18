## task_021_improve_accessibility_and_minimal_responsive_support - Improve accessibility and minimal responsive support
> From version: 0.1.0
> Schema version: 1.0
> Status: Ready
> Understanding: 90%
> Confidence: 85%
> Progress: 0%
> Complexity: Medium
> Theme: Implementation delivery
> Reminder: Update status/understanding/confidence/progress and linked request/backlog references when you edit this doc.

# Definition of Done (DoD)
- [ ] The backlog scope is implemented.
- [ ] Acceptance criteria are covered.
- [ ] Validation passes.
- [ ] Implementation, tests and documentation are delivered together in one dedicated commit for this task.

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

# Report
- Implementation complete.

# AI Context
- Summary: Implement improve accessibility and minimal responsive support.
- Keywords: task, implementation, backlog, runtime, python
- Use when: You need a bounded implementation task for a backlog item.
- Skip when: The work is still at the request or backlog shaping stage.

# Links
- Request: `req_007_finaliser_workflow_diagnostic_et_clarifier_cantracediag`
- Product brief(s): (none yet)
- Architecture decision(s): (none yet)
