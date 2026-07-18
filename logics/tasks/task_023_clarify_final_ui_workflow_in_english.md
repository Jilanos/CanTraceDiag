## task_023_clarify_final_ui_workflow_in_english - Clarify final UI workflow in English
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
- [ ] Implementation, tests and documentation are delivered together in one dedicated final commit for this task.

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

# Report
- Implementation complete.

# AI Context
- Summary: Implement clarify final ui workflow in english.
- Keywords: task, implementation, backlog, runtime, python
- Use when: You need a bounded implementation task for a backlog item.
- Skip when: The work is still at the request or backlog shaping stage.

# Links
- Request: `req_007_finaliser_workflow_diagnostic_et_clarifier_cantracediag`
- Product brief(s): (none yet)
- Architecture decision(s): (none yet)
