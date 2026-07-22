## task_021_migrer_l_ui_produit_vers_la_pwa_local_first_avec_parite_mvp - Migrer l UI produit vers la PWA local-first avec parite MVP
> From version: 1.0.0
> Schema version: 1.0
> Status: In progress
> Understanding: 90%
> Confidence: 85%
> Progress: 45%
> Complexity: High
> Theme: Implementation delivery
> Reminder: Update status/understanding/confidence/progress and linked request/backlog references when you edit this doc.
> Owner: codex

# Definition of Done (DoD)
- [ ] The backlog scope is implemented.
- [ ] Acceptance criteria are covered.
- [ ] Validation passes.
- [ ] Meaningful waves followed ADR 009: affected docs updated and the repo left commit-ready without automatic commits.

# Backlog
- `item_021_migrer_l_ui_produit_vers_la_pwa_local_first_avec_parite_mvp`

# Acceptance criteria
- AC1: Un inventaire exhaustif des fonctionnalités MVP de l'UI actuelle est
  établi depuis `src/cantracediag/web/app.js`, `src/cantracediag/web/index.html`
  et les endpoints `src/cantracediag/api.py`, avec statut `must-have`,
  `deferred` ou `obsolete`.
- AC2: Tous les appels `/api/...` utilisés par le MVP sont remplacés dans le
  chemin PWA par une abstraction `BackendPort` et une implémentation
  `LocalPwaBackend`; aucun fetch réseau applicatif vers FastAPI ne reste dans
  l'artefact PWA produit, hors chargement statique du manifest/assets/cache.
- AC3: Le rendu principal de l'UI PWA reprend la structure et l'ergonomie de
  l'interface actuelle plutôt que le rendu minimal du spike : zones d'import,
  progression, bibliothèque DBC/workspaces, liste de signaux, graphe/série,
  trace paginée, détails de frame et états d'erreur.
- AC4: Le moteur local atteint une parité MVP vérifiée pour import ASC + DBC,
  résolution de conflits DBC, status, import job/progress/cancel, signals,
  series, cursor, trace, trace-locate, frame-signals, purge et export demandé
  par le MVP.
- AC5: La persistance PWA utilise une stratégie adaptée aux gros fichiers :
  OPFS/IndexedDB ou équivalent pour traces/indexes/caches, et non `localStorage`
  pour des traces potentiellement volumineuses.
- AC6: Les fichiers ASC possibles jusqu'à 500 Mo sont traités par chunks et/ou
  workers dans le chemin produit, sans chargement complet durable en objets
  JavaScript et avec une voie de reprise/purge compréhensible.
- AC7: Une suite de tests de parité compare le comportement local PWA au backend
  Python de référence sur fixtures représentatives, y compris erreurs,
  conflits DBC et filtres principaux.
- AC8: Une smoke Chromium MVP démarre depuis le build statique, désactive ou
  absente FastAPI, importe les fixtures, exerce les workflows principaux et
  échoue si un appel réseau `/api/...` est observé.
- AC9: Les limites restantes avant déploiement public sont explicitement listées
  et visibles dans la documentation : DBC non couvert, navigateurs non validés,
  taille/performance, stratégie de migration des anciens workspaces et risques
  de stockage local.
- AC10: L'ancienne API FastAPI reste présente comme oracle/fallback pendant la
  migration, mais la documentation indique clairement à partir de quel signal
  elle pourra être retirée ou conservée uniquement comme mode local serveur.

# Validation
- Run `python3 -m logics_manager lint --require-status`.
- Use `python3 -m logics_manager flow progress task task_021_migrer_l_ui_produit_vers_la_pwa_local_first_avec_parite_mvp.md --progress <n>%` during multi-wave work.
- Run `python3 -m logics_manager flow finish task task_021_migrer_l_ui_produit_vers_la_pwa_local_first_avec_parite_mvp.md` after implementation.
- PASSED partial wave 2026-07-22: `node spikes/pwa-local-engine/build-browser.mjs`
  builds the product-shaped static PWA from the existing UI shell.
- PASSED partial wave 2026-07-22: `node --test
  spikes/pwa-local-engine/tests/*.test.ts` passed 9/9.
- PASSED partial wave 2026-07-22:
  `CTD_ENGINE_ROOT=spikes/pwa-local-engine/site CTD_ENGINE_PORT=9886
  CTD_ENGINE_DEBUG_PORT=9236 node spikes/pwa-local-engine/browser-smoke.mjs`
  imported `sample.asc` + `sample.dbc` from the product UI, selected
  `EngineSpeed`, rendered trace pagination, verified PWA manifest/service
  worker/cache, and observed zero `/api/...` network calls.

# Report
- Partial implementation wave completed on 2026-07-22.
- Product UI shell is now used by the static PWA build instead of the minimal
- Post-audit gate 2026-07-22: task_021 must not be closed as hosting-ready until request req_013_lever_les_bloquants_d_hebergement_pwa_full_frontend_post_audit_2026_07_22 and its P0 slices have been resolved or explicitly superseded. Source: docs/audit-refonte-full-frontend-2026-07-22.md.
  spike page.
- The build generates `product-app.mjs` from the current product `app.js` and
  replaces FastAPI network helpers with a browser-local adapter in
  `product-backend.ts`.
- Chromium smoke from the static build validates fixture import, status LED,
  signal explorer, trace table, selected signal plot state, DBC library,
  manifest, service worker, app-shell cache and no `/api/...` network calls.
- Remaining before this task can be closed: worker/chunk product import,
  OPFS/IndexedDB trace/index persistence, fuller DBC parity, conflict smoke,
  filter/cursor/inspector/export smoke coverage and product-scale benchmarks.
- New prerequisite identified on 2026-07-22: complete
  `task_022_rattraper_les_commits_ui_diagnostic_du_18_19_juillet_dans_la_pwa`
  so the PWA MVP includes the July 18/19 `origin/main` diagnostic UI features
  before this task is declared complete.
- Prerequisite update on 2026-07-22: `task_022` has implemented the recovery
  wave for workspace views, unified A/B measurements, report, CSV exports and
  cache freshness in the static PWA path. Remaining `task_021` closure work is
  now focused on large-file product import, durable storage, deeper DBC parity
  and product-scale validation.
- Evidence:
  `spikes/pwa-local-engine/product-mvp-inventory-2026-07-22.md` and
  `spikes/pwa-local-engine/product-migration-results-2026-07-22.md`.

# AI Context
- Summary: Implement the product migration from the current FastAPI-backed UI to
  the static local-first PWA, preserving the current visual MVP and replacing
  `/api/...` calls behind a browser-local backend.
- Keywords: task, pwa, local-first, ui-migration, product-parity, mvp,
  backend-port, local-backend, no-fastapi, opfs, indexeddb, chromium-smoke
- Use when: Starting or executing the next PWA milestone after the 0.1-0.3
  technical spikes.
- Skip when: Only changing the isolated spike UI or maintaining the old FastAPI
  local-server workflow.

# Links
- Request: `req_011_migrer_ui_produit_pwa_local_first_parite_mvp`
- Roadmap: `road_001_architecture_pwa_spa_local_first`
- Blocking recovery task: `task_022_rattraper_les_commits_ui_diagnostic_du_18_19_juillet_dans_la_pwa`
- Product brief(s): (none yet)
- Architecture decision(s): (none yet)
