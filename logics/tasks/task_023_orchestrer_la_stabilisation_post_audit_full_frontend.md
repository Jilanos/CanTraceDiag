## task_023_orchestrer_la_stabilisation_post_audit_full_frontend - Orchestrer la stabilisation post audit full frontend
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: Medium
> Theme: Implementation delivery
> Reminder: Update status/understanding/confidence/progress and linked request/backlog references when you edit this doc.
> Owner: codex

# Context
- Orchestrate the scaffolded request chain and keep sibling implementation slices linked.

# Plan
- [ ] 1. Commencer par la provenance afin de figer ce qui est source, genere et deployable.
- [ ] 2. Restaurer l oracle FastAPI et les tests serveur avant de comparer le moteur navigateur.
- [ ] 3. Corriger les trois bloquants de parite DBC navigateur puis traiter les divergences secondaires selon leur risque.
- [ ] 4. Reparer le cycle de vie service worker, la strategie de cache, le quota DBC et l installabilite.
- [ ] 5. Assembler le dossier de preuve go/no-go et mettre a jour task_021 avant toute decision d hebergement.
- [ ] ADR 009 checkpoint: update affected Logics docs during each meaningful wave and leave the repo commit-ready.
- [ ] Keep commit creation under operator control; do not force one commit per micro-step.
- [ ] GATE: do not close until lint, audit, and scaffold validation pass.

# Backlog
- `item_023_p0_etablir_provenance_et_packaging_de_la_refonte_pwa`
- `item_024_p0_restaurer_l_oracle_fastapi_et_les_tests_serveur`
- `item_025_p0_corriger_la_parite_dbc_navigateur_sur_traces_reelles`
- `item_026_p1_aligner_les_divergences_moteur_navigateur_non_bloquantes`
- `item_027_p0_fiabiliser_service_worker_cache_et_installabilite_pwa`
- `item_028_p1_produire_le_dossier_de_preuve_go_no_go_hebergement`

# Definition of Done (DoD)
- [x] Generated request, product, backlog, and task docs are present.
- [x] Context-pack handoff is available when requested.
- [x] Validation passes.
- [x] Meaningful waves followed ADR 009: affected docs updated and the repo left commit-ready without automatic commits.

# AC Traceability
- request-AC1 -> This task. Proof: scaffold command generated the request-chain corpus.
- request-AC4 -> This task. Proof: optional context-pack handoff is supported.
- request-AC6 -> This task. Proof: dry-run and collision checks bound file changes.
- request-AC8 -> This task. Proof: CLI help documents the one-pass scaffold workflow.
- request-AC2 -> This task. Evidence needed: Le produit FastAPI redevient un oracle fiable : /api/trace ne renvoie plus 500 au premier chargement, le middleware de securite accepte le contexte TestClient attendu, le code mort app.js contradictoire est retire ou neutralise, et la suite Python pertinente repasse au vert.
- request-AC3 -> This task. Evidence needed: Le moteur navigateur atteint la parite minimale trace reelle avec l oracle Python pour IDs etendus 29 bits, signaux Motorola/big-endian et multiplexage DBC, avec fixtures de regression representatives.
- request-AC5 -> This task. Evidence needed: Le cycle de vie PWA est deployable : service worker actualisable, strategie de cache coherente avec les noms d assets, garde de quota pour les DBC/workspaces et manifest avec icones raster 192 et 512.

# Validation
- Run `python3 -m logics_manager lint --require-status`.
- Run scaffold command tests.
- PASSED 2026-07-22: req_013 implementation chain completed. Functional proof: pytest targeted server suite 63 passed; node PWA suite 19 passed; build-browser passed; Chromium smoke on static site passed with manifest PNG icons, active versioned shell cache, CSV export and zero /api network calls. Workflow proof: logics-manager lint --require-status passed; targeted flow validate for req_013 and task_023-task_029 passed after closing sibling backlog items.
- Finish workflow executed on 2026-07-22.
- Linked backlog/request close verification passed.

# Report
- Implementation complete.
- Finished on 2026-07-22.
- Linked backlog item(s): `item_023_p0_etablir_provenance_et_packaging_de_la_refonte_pwa`, `item_024_p0_restaurer_l_oracle_fastapi_et_les_tests_serveur`, `item_025_p0_corriger_la_parite_dbc_navigateur_sur_traces_reelles`, `item_026_p1_aligner_les_divergences_moteur_navigateur_non_bloquantes`, `item_027_p0_fiabiliser_service_worker_cache_et_installabilite_pwa`, `item_028_p1_produire_le_dossier_de_preuve_go_no_go_hebergement`
- Related request(s): `req_013_lever_les_bloquants_d_hebergement_pwa_full_frontend_post_audit_2026_07_22`

# AI Context
- Summary: Orchestrer la stabilisation post audit full frontend
- Keywords: scaffolded-task, request-chain-scaffold, orchestration
- Use when: Coordinating implementation of a scaffolded request chain.
- Skip when: Working on one isolated sibling slice.

# Links
- Request: `req_013_lever_les_bloquants_d_hebergement_pwa_full_frontend_post_audit_2026_07_22`
- Product brief(s): `prod_003_gate_d_hebergement_pwa_full_frontend_post_audit`
- Architecture decision(s): (none yet)
