## task_009_p1_optimiser_endpoints_chauds - P1 Optimiser endpoints chauds
> From version: 1.0.0
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
- [ ] Meaningful waves followed ADR 009: affected docs updated and the repo left commit-ready without automatic commits.

# Backlog
- `item_009_p1_optimiser_endpoints_chauds`

# Acceptance criteria
- AC5: `/api/cursor` n'exécute plus de scan complet (plan de requête borné ou mesure
- AC6: La pagination de la trace est stable et déterministe : tri `(timestamp_s,

# AC Traceability
- request-AC5 -> This task. Proof: pending implementation of bounded cursor lookup and batch cursor endpoint.
- request-AC6 -> This task. Proof: pending implementation of stable deterministic trace pagination and locate consistency.

# Validation
- Run `python3 -m logics_manager lint --require-status`.
- Use `python3 -m logics_manager flow progress task task_009_p1_optimiser_endpoints_chauds.md --progress <n>%` during multi-wave work.
- Run `python3 -m logics_manager flow finish task task_009_p1_optimiser_endpoints_chauds.md` after implementation.

# Report
- Pending implementation.

# AI Context
- Summary: Implement p1 optimiser endpoints chauds.
- Keywords: task, implementation, backlog, runtime, python
- Use when: You need a bounded implementation task for a backlog item.
- Skip when: The work is still at the request or backlog shaping stage.

# Links
- Request: `req_003_robustesse_execution_et_completude_post_audit_2026_07_16`
- Product brief(s): (none yet)
- Architecture decision(s): (none yet)
