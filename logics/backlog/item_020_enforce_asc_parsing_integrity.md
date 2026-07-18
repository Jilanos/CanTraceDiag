## item_020_enforce_asc_parsing_integrity - Enforce ASC parsing integrity
> From version: 0.1.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: High
> Theme: Operator workflow and runtime integration
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
Le parseur accepte certains payloads incoherents avec leur DLC et ignore des formes
d'horodatage valides. Une anomalie ASC doit etre visible et ne jamais produire une
trame silencieusement tronquee ou corrompue.

# Scope
- In:
  - timestamps negatifs et scientifiques
  - validation stricte DLC/payload/octet pour le CAN classique
  - conservation des lignes horodatees invalides comme anomalies d'import
  - fixtures tronquees, surchargees et hors plage
- Out:
  - support CAN FD complet, BLF ou MF4
  - correction automatique des donnees invalides

# Acceptance criteria
- AC12: Une ligne ASC horodatee mais tronquee, un payload plus court ou plus long que

# AC Traceability
- request-AC12 -> This backlog slice. Proof: AC12: Une ligne ASC horodatee mais tronquee, un payload plus court ou plus long que

# Decision framing
- Product framing: Not needed
- Product signals: (none detected)
- Product follow-up: No product brief follow-up is expected based on current signals.
- Architecture framing: Not needed
- Architecture signals: (none detected)
- Architecture follow-up: No architecture decision follow-up is expected based on current signals.

# Links
- Product brief(s): (none yet)
- Architecture decision(s): (none yet)
- Request: `logics/request/req_007_finaliser_workflow_diagnostic_et_clarifier_cantracediag.md`
- Primary task(s): (none yet)

# AI Context
- Summary: Enforce ASC parsing integrity
- Keywords: backlog-groom, request, enforce asc parsing integrity, bounded slice
- Use when: Use when implementing or reviewing the delivery slice for Enforce ASC parsing integrity.
- Skip when: Skip when the change is unrelated to this delivery slice or its linked request.

# Priority
- Priority: High
- Rationale: L'integrite des donnees conditionne la confiance dans tout diagnostic exporte.

# Notes
- Hybrid rationale: Derived from request `req_007_finaliser_workflow_diagnostic_et_clarifier_cantracediag` and kept bounded to one coherent delivery slice.
- Source file: `logics/request/req_007_finaliser_workflow_diagnostic_et_clarifier_cantracediag.md`.
- Generated locally by logics-manager.
- Task `task_020_enforce_asc_parsing_integrity` was finished via `logics-manager flow finish task` on 2026-07-18.

# Tasks
- `task_020_enforce_asc_parsing_integrity`
