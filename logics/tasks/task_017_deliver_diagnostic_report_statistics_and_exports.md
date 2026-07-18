## task_017_deliver_diagnostic_report_statistics_and_exports - Deliver diagnostic report statistics and exports
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
- Sequence: 1 of 7; this is the first implementation task.
- Commit only AC1-AC3 and their tests/docs; do not include work from tasks 018-023.
- Suggested commit: `feat(diagnostic): add report statistics and exports`.

# Backlog
- `item_017_deliver_diagnostic_report_statistics_and_exports`

# Acceptance criteria
- AC1: Une vue `Report` fournit une synthese de l'import avec le fichier analyse, la
- AC2: L'utilisateur exporte en CSV et Parquet les signaux selectionnes sur la plage
- AC3: La vue `Analysis` affiche par signal numerique selectionne le nombre

# Validation
- Run focused backend/API/export tests, including bounded-memory export coverage.
- Run the full Python suite and `ruff check .`.
- Run `python3 -m logics_manager lint --require-status`.
- Use `python3 -m logics_manager flow progress task task_017_deliver_diagnostic_report_statistics_and_exports.md --progress <n>%` during multi-wave work.
- Run `python3 -m logics_manager flow finish task task_017_deliver_diagnostic_report_statistics_and_exports.md` after implementation.

# Report
- Implementation complete.

# AI Context
- Summary: Implement deliver diagnostic report statistics and exports.
- Keywords: task, implementation, backlog, runtime, python
- Use when: You need a bounded implementation task for a backlog item.
- Skip when: The work is still at the request or backlog shaping stage.

# Links
- Request: `req_007_finaliser_workflow_diagnostic_et_clarifier_cantracediag`
- Product brief(s): (none yet)
- Architecture decision(s): (none yet)
