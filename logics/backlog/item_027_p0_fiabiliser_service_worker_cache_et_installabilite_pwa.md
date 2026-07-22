## item_027_p0_fiabiliser_service_worker_cache_et_installabilite_pwa - P0 fiabiliser service worker cache et installabilite PWA
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: Medium
> Theme: Static hosting readiness
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- Le service worker a un CACHE_NAME fige et un cache-first qui peut bloquer les visiteurs sur une ancienne version meme apres hard-refresh.
- Les assets JS sans hash aggravent le risque de stale shell.
- saveDbcs peut lever QuotaExceededError sans garde et le manifest ne fournit pas d icones PNG 192/512.

# Scope
- In:
  - Introduire une strategie d actualisation service worker reproductible : cache versionne par build, assets hashes ou network-first/stale-while-revalidate coherent.
  - Verifier que index.html et les modules JS ne restent pas indefiniment perimes apres nouveau build.
  - Rattraper la garde de quota pour saveDbcs dans le backend local actif.
  - Ajouter des icones raster PWA 192x192 et 512x512 et les declarer dans le manifest.
  - Etendre la smoke Chromium pour detecter l actualisation du shell et les erreurs de quota.
- Out:
  - Mettre en place une CDN ou une strategie multi-version complexe.
  - Migrer tout le stockage gros fichiers vers OPFS dans cette tranche si deja couvert par task_021.
  - Deployer effectivement le site.

# Acceptance criteria
- AC1: Deux builds successifs avec changement JS provoquent une mise a jour observable du shell PWA.
- AC2: Le service worker purge les caches obsoletes sans bloquer les navigations sur un ancien index.html.
- AC3: Les DBC volumineux ou le quota localStorage insuffisant produisent une erreur geree et une voie de recuperation.
- AC4: Le manifest declare des PNG 192x192 et 512x512 generes depuis une source versionnee.
- AC5: La smoke statique valide manifest, service worker, cache freshness et absence d appel reseau /api applicatif.

# AC Traceability
- request-AC5 -> This backlog slice. Proof: AC1: Deux builds successifs avec changement JS provoquent une mise a jour observable du shell PWA.
- request-AC6 -> This backlog slice. Proof: AC2: Le service worker purge les caches obsoletes sans bloquer les navigations sur un ancien index.html.
- request-AC3 -> This backlog slice. Evidence needed: Le moteur navigateur atteint la parite minimale trace reelle avec l oracle Python pour IDs etendus 29 bits, signaux Motorola/big-endian et multiplexage DBC, avec fixtures de regression representatives.
- request-AC4 -> This backlog slice. Evidence needed: Les divergences fonctionnelles restantes du moteur navigateur sont soit corrigees soit documentees avec decision explicite : locateRow, DBC dupliques, parsing ASC strict, filtres trace_rows, decimation signalSeries, contrat signalStats et limites de decode_error.

# Decision framing
- Product framing: Not needed
- Architecture framing: Not needed

# Links
- Product brief(s): `prod_003_gate_d_hebergement_pwa_full_frontend_post_audit`
- Architecture decision(s): (none yet)
- Request: `req_013_lever_les_bloquants_d_hebergement_pwa_full_frontend_post_audit_2026_07_22`
- Primary task(s): `task_023_orchestrer_la_stabilisation_post_audit_full_frontend`

# AI Context
- Summary: P0 fiabiliser service worker cache et installabilite PWA
- Keywords: scaffolded-backlog, p0 fiabiliser service worker cache et installabilite pwa, implementation-ready
- Use when: Implementing the scaffolded slice for P0 fiabiliser service worker cache et installabilite PWA.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: High
- Rationale: Set by scaffold input or defaulted for grooming.

# Tasks
- `task_028_p0_fiabiliser_service_worker_cache_et_installabilite_pwa`

# Notes
- Task `task_028_p0_fiabiliser_service_worker_cache_et_installabilite_pwa` was finished via `logics-manager flow finish task` on 2026-07-22.
- Task `task_023_orchestrer_la_stabilisation_post_audit_full_frontend` was finished via `logics-manager flow finish task` on 2026-07-22.
