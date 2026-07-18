## task_013_p2_reduire_dette_parsing_maintenance_ci - P2 Reduire dette parsing maintenance CI
> From version: 1.0.0
> Schema version: 1.0
> Status: Obsolete
> Understanding: 100%
> Confidence: 99%
> Progress: 0%
> Complexity: Medium
> Theme: Implementation delivery
> Reminder: Update status/understanding/confidence/progress and linked request/backlog references when you edit this doc.

# Definition of Done (DoD)
- [x] Withdrawn before implementation; no delivery is claimed.
- [x] Replacement request is linked in the workflow indicators.
- [x] No code or validation proof is attributed to this obsolete task.
- [x] Remaining scope is split between `task_020_enforce_asc_parsing_integrity` and
  `task_022_modularize_frontend_and_align_dependencies_ci_and_docs`.

# Backlog
- `item_013_p2_reduire_dette_parsing_maintenance_ci`

# Acceptance criteria
- AC13: Une ligne ASC tronquée ou avec attributs de fin de ligne produit un événement
- AC14: `pyarrow` et `python-can` sont utilisés ou retirés ; le code mort identifié
- AC15: La CI échoue si les E2E sont skippés faute de navigateur, et protège un budget

# AC Traceability
- request-AC13 -> This task. Proof: pending implementation of robust ASC parsing for truncated lines, trailing attributes, negative/scientific timestamps, and DLC bounds.
- request-AC14 -> This task. Proof: pending implementation of dependency/code-debt cleanup and ES module split.
- request-AC15 -> This task. Proof: pending implementation of non-skipped E2E CI enforcement and synthetic import budget checks.

# Validation
- Run `python3 -m logics_manager lint --require-status`.
- Use `python3 -m logics_manager flow progress task task_013_p2_reduire_dette_parsing_maintenance_ci.md --progress <n>%` during multi-wave work.
- Run `python3 -m logics_manager flow finish task task_013_p2_reduire_dette_parsing_maintenance_ci.md` after implementation.

# Report
- Pending implementation.

# AI Context
- Summary: Implement p2 reduire dette parsing maintenance ci.
- Keywords: task, implementation, backlog, runtime, python
- Use when: You need a bounded implementation task for a backlog item.
- Skip when: The work is still at the request or backlog shaping stage.

# Links
- Request: `req_003_robustesse_execution_et_completude_post_audit_2026_07_16`
- Product brief(s): (none yet)
- Architecture decision(s): (none yet)
- Superseded by: `req_007_finaliser_workflow_diagnostic_et_clarifier_cantracediag`
