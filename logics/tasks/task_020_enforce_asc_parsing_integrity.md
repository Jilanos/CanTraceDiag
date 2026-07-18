## task_020_enforce_asc_parsing_integrity - Enforce ASC parsing integrity
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
- Sequence: 4 of 7; start after task 019 is complete.
- Commit only AC12 and its fixtures/tests/docs; do not include later slices.
- Suggested commit: `fix(asc): preserve and report malformed trace lines`.

# Backlog
- `item_020_enforce_asc_parsing_integrity`

# Acceptance criteria
- AC12: Une ligne ASC horodatee mais tronquee, un payload plus court ou plus long que

# Validation
- Run negative/scientific timestamp and malformed DLC/payload parser tests.
- Run the full Python suite and `ruff check .`.
- Run `python3 -m logics_manager lint --require-status`.
- Use `python3 -m logics_manager flow progress task task_020_enforce_asc_parsing_integrity.md --progress <n>%` during multi-wave work.
- Run `python3 -m logics_manager flow finish task task_020_enforce_asc_parsing_integrity.md` after implementation.

# Report
- Implementation complete.

# AI Context
- Summary: Implement enforce asc parsing integrity.
- Keywords: task, implementation, backlog, runtime, python
- Use when: You need a bounded implementation task for a backlog item.
- Skip when: The work is still at the request or backlog shaping stage.

# Links
- Request: `req_007_finaliser_workflow_diagnostic_et_clarifier_cantracediag`
- Product brief(s): (none yet)
- Architecture decision(s): (none yet)
