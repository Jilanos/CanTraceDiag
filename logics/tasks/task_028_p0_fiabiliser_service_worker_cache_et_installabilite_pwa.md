## task_028_p0_fiabiliser_service_worker_cache_et_installabilite_pwa - P0 fiabiliser service worker cache et installabilite PWA
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
- `item_027_p0_fiabiliser_service_worker_cache_et_installabilite_pwa`

# Acceptance criteria
- AC1: Deux builds successifs avec changement JS provoquent une mise a jour observable du shell PWA.
- AC2: Le service worker purge les caches obsoletes sans bloquer les navigations sur un ancien index.html.
- AC3: Les DBC volumineux ou le quota localStorage insuffisant produisent une erreur geree et une voie de recuperation.
- AC4: Le manifest declare des PNG 192x192 et 512x512 generes depuis une source versionnee.
- AC5: La smoke statique valide manifest, service worker, cache freshness et absence d appel reseau /api applicatif.

# Validation
- Run `python3 -m logics_manager lint --require-status`.
- Use `python3 -m logics_manager flow progress task task_028_p0_fiabiliser_service_worker_cache_et_installabilite_pwa.md --progress <n>%` during multi-wave work.
- Run `python3 -m logics_manager flow finish task task_028_p0_fiabiliser_service_worker_cache_et_installabilite_pwa.md` after implementation.
- PASSED 2026-07-22: node --test spikes/pwa-local-engine/tests/*.test.ts -> 13 passed, including Local product backend quota recovery. PASSED: node spikes/pwa-local-engine/build-browser.mjs injects a versioned cantracediag-pwa-shell-<hash> cache name. PASSED: CTD_ENGINE_ROOT=spikes/pwa-local-engine/site CTD_ENGINE_PORT=9893 CTD_ENGINE_DEBUG_PORT=9243 node spikes/pwa-local-engine/browser-smoke.mjs validated manifest PNG icons 192/512, active service worker, versioned shell cache, CSV export, and zero /api network calls.
- Finish workflow executed on 2026-07-22.
- Linked backlog/request close verification passed.

# Report
- Implementation complete.
- Finished on 2026-07-22.
- Linked backlog item(s): `item_027_p0_fiabiliser_service_worker_cache_et_installabilite_pwa`
- Related request(s): `req_013_lever_les_bloquants_d_hebergement_pwa_full_frontend_post_audit_2026_07_22`

# AI Context
- Summary: Implement p0 fiabiliser service worker cache et installabilite pwa.
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
