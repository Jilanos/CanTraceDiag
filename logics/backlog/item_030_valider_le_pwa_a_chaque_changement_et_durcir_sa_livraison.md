## item_030_valider_le_pwa_a_chaque_changement_et_durcir_sa_livraison - Valider le PWA a chaque changement et durcir sa livraison
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: Medium
> Theme: quality
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- La CI ne construit ni ne teste le PWA sur les PR.
- Le build depend de scripts fragiles et la livraison Nginx manque de protections.

# Scope
- In:
  - CI Node 22 pour lint, tests, build et smoke test PWA
  - Fiabilisation des assets de l'app shell
  - En-tetes Nginx de securite et cache explicites
- Out:
  - Refonte fonctionnelle de l'interface

# Acceptance criteria
- Une PR PWA echoue si lint, tests, build ou smoke test echoue.
- L'image livree expose des en-tetes de securite et de cache verifies.

# AC Traceability
- request-Chaque lot prioritaire de l'audit est couvert par un backlog et une tache tracable. -> This backlog slice. Proof: Une PR PWA echoue si lint, tests, build ou smoke test echoue.

# Decision framing
- Product framing: Not needed
- Architecture framing: Not needed

# Links
- Product brief(s): `prod_004_fiabilisation_du_produit_cantracediag`
- Architecture decision(s): (none yet)
- Request: `req_015_remedier_aux_constats_de_l_audit_technique_2026_07_25`
- Primary task(s): `task_031_orchestrer_la_remediation_de_l_audit_cantracediag`

# AI Context
- Summary: Valider le PWA a chaque changement et durcir sa livraison
- Keywords: scaffolded-backlog, valider le pwa a chaque changement et durcir sa livraison, implementation-ready
- Use when: Implementing the scaffolded slice for Valider le PWA a chaque changement et durcir sa livraison.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: high
- Rationale: Set by scaffold input or defaulted for grooming.

# Tasks
- `task_032_valider_le_pwa_a_chaque_changement_et_durcir_sa_livraison`

# Notes
- Task `task_032_valider_le_pwa_a_chaque_changement_et_durcir_sa_livraison` was finished via `logics-manager flow finish task` on 2026-07-25.
