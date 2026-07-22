## req_013_lever_les_bloquants_d_hebergement_pwa_full_frontend_post_audit_2026_07_22 - Lever les bloquants d hebergement PWA full frontend post audit 2026 07 22
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Complexity: High
> Theme: Post-audit release hardening
> Reminder: Update status/understanding/confidence and linked backlog/task references when you edit this doc.

# Needs
- Transformer les constats de l audit full frontend du 22 juillet 2026 en chaine Logics executable avant tout hebergement public.
- Retablir un oracle FastAPI fiable avant de s en servir comme reference de parite pour la PWA navigateur.
- Garantir que la PWA statique ne livre pas de resultats faux sur des traces reelles courantes et qu elle reste actualisable apres deploiement.
- Produire une preuve de provenance, de tests et de limites residuelles suffisante pour decider ensuite d un deploiement public.

# Context
- L audit conclut que la refonte full frontend n est pas prete a heberger malgre une architecture globalement saine.
- La branche feat/pwa-local-first contient la refonte en working tree non commite ; l artefact deployable vit dans spikes/pwa-local-engine/site/ et n a pas de provenance versionnee.
- Les bloquants identifies couvrent quatre familles : regressions FastAPI, parite DBC navigateur, cycle de vie service worker/cache et dette de packaging/installabilite.
- Les chaines Logics PWA existantes task_020 et task_022 sont Done, mais l audit post-verification revele des conditions de fermeture insuffisantes pour un hebergement public.
- La tache task_021 reste In progress et doit consommer cette chaine comme gate de stabilisation avant fermeture MVP.

# Acceptance criteria
- AC1: La refonte a une provenance versionnee claire : les sources deployables sont suivies, le build est reproductible depuis ces sources et l artefact site/ n est pas la seule source de verite.
- AC2: Le produit FastAPI redevient un oracle fiable : /api/trace ne renvoie plus 500 au premier chargement, le middleware de securite accepte le contexte TestClient attendu, le code mort app.js contradictoire est retire ou neutralise, et la suite Python pertinente repasse au vert.
- AC3: Le moteur navigateur atteint la parite minimale trace reelle avec l oracle Python pour IDs etendus 29 bits, signaux Motorola/big-endian et multiplexage DBC, avec fixtures de regression representatives.
- AC4: Les divergences fonctionnelles restantes du moteur navigateur sont soit corrigees soit documentees avec decision explicite : locateRow, DBC dupliques, parsing ASC strict, filtres trace_rows, decimation signalSeries, contrat signalStats et limites de decode_error.
- AC5: Le cycle de vie PWA est deployable : service worker actualisable, strategie de cache coherente avec les noms d assets, garde de quota pour les DBC/workspaces et manifest avec icones raster 192 et 512.
- AC6: Les preuves pre-hebergement couvrent build statique, tests unitaires/parite, smoke Chromium sans appel /api reseau, validation Logics, documentation des limites restantes et decision explicite go/no-go.

# Definition of Ready (DoR)
- [x] Problem statement is explicit and user impact is clear.
- [x] Scope boundaries (in/out) are explicit.
- [x] Acceptance criteria are testable.
- [x] Dependencies and known risks are listed.

# Companion docs
- Product brief(s): `prod_003_gate_d_hebergement_pwa_full_frontend_post_audit`
- Architecture decision(s): (none yet)

# References
- docs/audit-refonte-full-frontend-2026-07-22.md
- logics/tasks/task_021_migrer_l_ui_produit_vers_la_pwa_local_first_avec_parite_mvp.md
- logics/tasks/task_020_pwa_statique_deployable_local_first.md
- logics/tasks/task_022_rattraper_les_commits_ui_diagnostic_du_18_19_juillet_dans_la_pwa.md
- spikes/pwa-local-engine/
- src/cantracediag/api.py
- src/cantracediag/store.py
- src/cantracediag/security.py
- src/cantracediag/web/

# AI Context
- Summary: Lever les bloquants d hebergement PWA full frontend post audit 2026 07 22
- Keywords: request-chain-scaffold, lever les bloquants d hebergement pwa full frontend post audit 2026 07 22, development-ready
- Use when: You need to implement or review the scaffolded workflow for Lever les bloquants d hebergement PWA full frontend post audit 2026 07 22.
- Skip when: The change is unrelated to this scaffolded request chain.

# Backlog
- `item_023_p0_etablir_provenance_et_packaging_de_la_refonte_pwa`
- `item_024_p0_restaurer_l_oracle_fastapi_et_les_tests_serveur`
- `item_025_p0_corriger_la_parite_dbc_navigateur_sur_traces_reelles`
- `item_026_p1_aligner_les_divergences_moteur_navigateur_non_bloquantes`
- `item_027_p0_fiabiliser_service_worker_cache_et_installabilite_pwa`
- `item_028_p1_produire_le_dossier_de_preuve_go_no_go_hebergement`
