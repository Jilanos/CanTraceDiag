## task_031_orchestrer_la_remediation_de_l_audit_cantracediag - Orchestrer la remediation de l'audit CanTraceDiag
> From version: 1.0.0
> Schema version: 1.0
> Status: In progress
> Understanding: 90%
> Confidence: 85%
> Progress: 33%
> Complexity: Medium
> Theme: Implementation delivery
> Reminder: Update status/understanding/confidence/progress and linked request/backlog references when you edit this doc.
> Owner: codex

# Context
- Orchestrate the scaffolded request chain and keep sibling implementation slices linked.

# Plan
- [ ] 1. Traiter la chaine CI et livraison
- [ ] 2. Stabiliser l'architecture canonique
- [ ] 3. Clore la gouvernance et la supply chain
- [ ] ADR 009 checkpoint: update affected Logics docs during each meaningful wave and leave the repo commit-ready.
- [ ] Keep commit creation under operator control; do not force one commit per micro-step.
- [ ] GATE: do not close until lint, audit, and scaffold validation pass.

# Backlog
- `item_030_valider_le_pwa_a_chaque_changement_et_durcir_sa_livraison`
- `item_031_rendre_l_architecture_pwa_canonique_et_testable`
- `item_032_retablir_la_gouvernance_logics_et_la_securite_de_la_release`

# Definition of Done (DoD)
- [ ] Generated request, product, backlog, and task docs are present.
- [ ] Context-pack handoff is available when requested.
- [ ] Validation passes.
- [ ] Meaningful waves followed ADR 009: affected docs updated and the repo left commit-ready without automatic commits.

# AC Traceability
- request-AC1 -> This task. Proof: scaffold command generated the request-chain corpus.
- request-AC4 -> This task. Proof: optional context-pack handoff is supported.
- request-AC6 -> This task. Proof: dry-run and collision checks bound file changes.
- request-AC8 -> This task. Proof: CLI help documents the one-pass scaffold workflow.

# Validation
- Run `python3 -m logics_manager lint --require-status`.
- Run scaffold command tests.
- Lot 1 valide: CI distante verte, publication image reussie, tag v1.0.0 pousse. Blocage de cloture: le workflow de deploiement echoue avant connexion avec ; aucun secret GitHub n'est configure. Reprendre apres ajout de VPS_HOST, VPS_USER, VPS_SSH_KEY et VPS_SSH_PORT puis reexecuter le workflow de release.
- Precision: le workflow de deploiement echoue avant connexion avec l erreur "missing server host"; aucun secret GitHub n est configure.

# Report
- Implementation complete.

# AI Context
- Summary: Orchestrer la remediation de l'audit CanTraceDiag
- Keywords: scaffolded-task, request-chain-scaffold, orchestration
- Use when: Coordinating implementation of a scaffolded request chain.
- Skip when: Working on one isolated sibling slice.

# Links
- Request: `req_015_remedier_aux_constats_de_l_audit_technique_2026_07_25`
- Product brief(s): `prod_004_fiabilisation_du_produit_cantracediag`
- Architecture decision(s): (none yet)

# Notes
- Regle de cloture de la chaine: une fois les criteres d'acceptation valides, preparer la version 1.0.0, creer un commit atomique des changements Logics et code, puis pousser la branche et le commit. Attendre la fin de la CI; uniquement si elle est verte, creer et pousser le tag v1.0.0. Suivre le deploiement jusqu'a sa disponibilite et corriger tout incident ou regression avant de declarer la release terminee.
