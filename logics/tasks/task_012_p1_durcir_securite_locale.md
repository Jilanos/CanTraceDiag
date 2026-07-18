## task_012_p1_durcir_securite_locale - P1 Durcir securite locale
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
- [x] Replacement task is linked in the workflow indicators.
- [x] No code or validation proof is attributed to this obsolete task.
- [x] Remaining scope is carried by `task_019_harden_local_and_lan_api_security`.

# Backlog
- `item_011_p1_durcir_securite_locale`

# Acceptance criteria
- AC11: L'API rejette les requêtes dont le Host n'est pas dans l'allowlist locale et

# AC Traceability
- request-AC11 -> This task. Proof: pending implementation of local host/origin/token/upload-limit protections.

# Validation
- Run `python3 -m logics_manager lint --require-status`.
- Use `python3 -m logics_manager flow progress task task_012_p1_durcir_securite_locale.md --progress <n>%` during multi-wave work.
- Run `python3 -m logics_manager flow finish task task_012_p1_durcir_securite_locale.md` after implementation.

# Report
- Pending implementation.

# AI Context
- Summary: Implement p1 durcir securite locale.
- Keywords: task, implementation, backlog, runtime, python
- Use when: You need a bounded implementation task for a backlog item.
- Skip when: The work is still at the request or backlog shaping stage.

# Links
- Request: `req_003_robustesse_execution_et_completude_post_audit_2026_07_16`
- Product brief(s): (none yet)
- Architecture decision(s): (none yet)
- Superseded by: `task_019_harden_local_and_lan_api_security`
