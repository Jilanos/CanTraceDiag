## req_015_remedier_aux_constats_de_l_audit_technique_2026_07_25 - Remedier aux constats de l'audit technique 2026-07-25
> From version: 1.0.0
> Schema version: 1.0
> Status: Draft
> Understanding: 90%
> Confidence: 85%
> Complexity: High
> Theme: reliability
> Reminder: Update status/understanding/confidence and linked backlog/task references when you edit this doc.
> Indicators reviewed: 2026-08-21 10:06:05

# Needs
- Valider le PWA sur chaque changement
- Unifier l'architecture produit et la livraison
- Retablir une gouvernance et une chaine de livraison verifiables

# Context
- L'audit identifie une divergence entre l'application Python et le PWA statique, une CI PWA insuffisante et des ecarts Logics historiques.

# Acceptance criteria
- Chaque lot prioritaire de l'audit est couvert par un backlog et une tache tracable.
- Les travaux de securite, de CI et d'architecture sont ordonnes par risque.

# Definition of Ready (DoR)
- [x] Problem statement is explicit and user impact is clear.
- [x] Scope boundaries (in/out) are explicit.
- [x] Acceptance criteria are testable.
- [x] Dependencies and known risks are listed.

# Companion docs
- Product brief(s): `prod_004_fiabilisation_du_produit_cantracediag`
- Architecture decision(s): (none yet)

# References
- AUDIT_TECHNIQUE.md

# AI Context
- Summary: Remedier aux constats de l'audit technique 2026-07-25
- Keywords: audit-technique, pwa-ci, architecture-canonique, gouvernance-logics, supply-chain-release
- Use when: You need to plan or review remediation of the PWA CI, canonical architecture, Logics governance, or release supply chain identified by the 2026-07-25 audit.
- Skip when: The work does not address a finding from this audit.

# Backlog
- `item_030_valider_le_pwa_a_chaque_changement_et_durcir_sa_livraison`
- `item_031_rendre_l_architecture_pwa_canonique_et_testable`
- `item_032_retablir_la_gouvernance_logics_et_la_securite_de_la_release`
