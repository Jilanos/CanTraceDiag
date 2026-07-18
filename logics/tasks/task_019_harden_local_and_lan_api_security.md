## task_019_harden_local_and_lan_api_security - Harden local and LAN API security
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
- Sequence: 3 of 7; start after task 018 is complete.
- Commit only AC10-AC11 and their hostile tests/docs; do not include later slices.
- Suggested commit: `security(api): protect local and LAN access`.

# Backlog
- `item_019_harden_local_and_lan_api_security`

# Acceptance criteria
- AC10: L'API rejette un Host ou une Origin non autorises, exige un jeton de session
- AC11: L'import par chemin serveur est desactive hors boucle locale ou derriere une

# Validation
- Run Host, Origin, token, upload-limit and LAN path-import hostile tests.
- Run the full Python suite and `ruff check .`.
- Run `python3 -m logics_manager lint --require-status`.
- Use `python3 -m logics_manager flow progress task task_019_harden_local_and_lan_api_security.md --progress <n>%` during multi-wave work.
- Run `python3 -m logics_manager flow finish task task_019_harden_local_and_lan_api_security.md` after implementation.

# Report
- Implementation complete.

# AI Context
- Summary: Implement harden local and lan api security.
- Keywords: task, implementation, backlog, runtime, python
- Use when: You need a bounded implementation task for a backlog item.
- Skip when: The work is still at the request or backlog shaping stage.

# Links
- Request: `req_007_finaliser_workflow_diagnostic_et_clarifier_cantracediag`
- Product brief(s): (none yet)
- Architecture decision(s): (none yet)
