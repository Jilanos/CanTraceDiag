## item_031_rendre_l_architecture_pwa_canonique_et_testable - Rendre l'architecture PWA canonique et testable
> From version: 1.0.0
> Schema version: 1.0
> Status: In progress
> Understanding: 90%
> Confidence: 85%
> Progress: 5%
> Complexity: High
> Theme: architecture
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- Deux interfaces divergent et le flux de donnees PWA reste base sur des parcours de prototype.

# Scope
- In:
  - Choix documente de l'interface canonique
  - Contrat de transport et etats d'erreur testes
  - Parite des parcours ou retrait explicite de la voie non canonique
  - Documentation d'execution et de deploiement
- Out:
  - Changement du modele clinique

# Acceptance criteria
- Un seul parcours produit est declare canonique.
- Les donnees reelles, les erreurs et les etats vides sont testes sur ce parcours.

# AC Traceability
- request-Les travaux de securite, de CI et d'architecture sont ordonnes par risque. -> This backlog slice. Proof: Un seul parcours produit est declare canonique.

# Decision framing
- Product framing: Not needed
- Architecture framing: Not needed

# Links
- Product brief(s): `prod_004_fiabilisation_du_produit_cantracediag`
- Architecture decision(s): (none yet)
- Request: `req_015_remedier_aux_constats_de_l_audit_technique_2026_07_25`
- Primary task(s): `task_031_orchestrer_la_remediation_de_l_audit_cantracediag`

# AI Context
- Summary: Rendre l'architecture PWA canonique et testable
- Keywords: scaffolded-backlog, rendre l'architecture pwa canonique et testable, implementation-ready
- Use when: Implementing the scaffolded slice for Rendre l'architecture PWA canonique et testable.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: high
- Rationale: Set by scaffold input or defaulted for grooming.

# Tasks
- `task_033_rendre_l_architecture_pwa_canonique_et_testable`
