## task_029_p1_produire_le_dossier_de_preuve_go_no_go_hebergement - P1 produire le dossier de preuve go no go hebergement
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

# Definition of Done (DoD)
- [x] The backlog scope is implemented.
- [x] Acceptance criteria are covered.
- [x] Validation passes.
- [x] Meaningful waves followed ADR 009: affected docs updated and the repo left commit-ready without automatic commits.

# Backlog
- `item_028_p1_produire_le_dossier_de_preuve_go_no_go_hebergement`

# Acceptance criteria
- AC1: Un document de preuve post-audit liste les commandes executees, resultats, artefacts et references Logics.
- AC2: Les limites residuelles avant hebergement sont listees avec niveau de risque et decision.
- AC3: Le statut de task_021 est coherent avec ce qui reste hors gate hebergement.
- AC4: logics-manager lint --require-status et logics-manager audit --group-by-doc passent ou leurs anomalies sont classees.
- AC5: La decision go/no-go mentionne explicitement le domaine cible et la date.

# Validation
- Run `python3 -m logics_manager lint --require-status`.
- Use `python3 -m logics_manager flow progress task task_029_p1_produire_le_dossier_de_preuve_go_no_go_hebergement.md --progress <n>%` during multi-wave work.
- Run `python3 -m logics_manager flow finish task task_029_p1_produire_le_dossier_de_preuve_go_no_go_hebergement.md` after implementation.
- PASSED 2026-07-22: evidence document docs/pwa-full-frontend-post-audit-evidence-2026-07-22.md created. PASSED: pytest targeted server suite 63 passed; node PWA suite 19 passed; static build passed; Chromium smoke passed with zero /api network calls; logics-manager lint --require-status passed; req_013 targeted flow validate passed with 0 findings. Global audit still has historical blockers outside req_013 and one non-blocking prod_003 Mermaid warning, classified in the evidence document.
- Finish workflow executed on 2026-07-22.
- Linked backlog/request close verification passed.

# Report
- Implementation complete.
- Finished on 2026-07-22.
- Linked backlog item(s): `item_028_p1_produire_le_dossier_de_preuve_go_no_go_hebergement`
- Related request(s): `req_013_lever_les_bloquants_d_hebergement_pwa_full_frontend_post_audit_2026_07_22`

# AI Context
- Summary: Implement p1 produire le dossier de preuve go no go hebergement.
- Keywords: task, implementation, backlog, runtime, python
- Use when: You need a bounded implementation task for a backlog item.
- Skip when: The work is still at the request or backlog shaping stage.

# Links
- Request: `req_013_lever_les_bloquants_d_hebergement_pwa_full_frontend_post_audit_2026_07_22`
- Product brief(s): (none yet)
- Architecture decision(s): (none yet)

# AC Traceability
- request-AC1 -> This task. Evidence needed: La refonte a une provenance versionnee claire : les sources deployables sont suivies, le build est reproductible depuis ces sources et l artefact site/ n est pas la seule source de verite.
- request-AC2 -> This task. Evidence needed: Le produit FastAPI redevient un oracle fiable : /api/trace ne renvoie plus 500 au premier chargement, le middleware de securite accepte le contexte TestClient attendu, le code mort app.js contradictoire est retire ou neutralise, et la suite Python pertinente repasse au vert.
- request-AC3 -> This task. Evidence needed: Le moteur navigateur atteint la parite minimale trace reelle avec l oracle Python pour IDs etendus 29 bits, signaux Motorola/big-endian et multiplexage DBC, avec fixtures de regression representatives.
- request-AC4 -> This task. Evidence needed: Les divergences fonctionnelles restantes du moteur navigateur sont soit corrigees soit documentees avec decision explicite : locateRow, DBC dupliques, parsing ASC strict, filtres trace_rows, decimation signalSeries, contrat signalStats et limites de decode_error.
- request-AC5 -> This task. Evidence needed: Le cycle de vie PWA est deployable : service worker actualisable, strategie de cache coherente avec les noms d assets, garde de quota pour les DBC/workspaces et manifest avec icones raster 192 et 512.
- request-AC6 -> This task. Evidence needed: Les preuves pre-hebergement couvrent build statique, tests unitaires/parite, smoke Chromium sans appel /api reseau, validation Logics, documentation des limites restantes et decision explicite go/no-go.
