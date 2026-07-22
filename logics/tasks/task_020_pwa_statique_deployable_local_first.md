## task_020_pwa_statique_deployable_local_first - PWA statique deployable local-first
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
- `item_020_pwa_statique_deployable_local_first`

# Acceptance criteria
- AC1: Un build statique reproductible produit un répertoire distribuable
  contenant HTML, JS, CSS, manifest PWA, service worker et assets nécessaires.
- AC2: L'application fonctionne depuis un serveur statique local sans FastAPI :
  import trace + DBC, status, signaux, trace paginée, série sélectionnée et purge.
- AC3: Le shell PWA est installable/offline : manifest valide, service worker
  enregistré, cache de l'app shell et stratégie claire pour ne pas cacher des
  traces utilisateur par erreur.
- AC4: Une gestion de workspaces locale minimale existe : liste, reprise,
  suppression, purge globale et export/import portable d'un workspace de fixture
  ou format documenté si l'export complet est volontairement différé.
- AC5: Les erreurs de quota/stockage local sont détectées ou simulables et
  présentées avec une voie de récupération compréhensible.
- AC6: La documentation de déploiement statique couvre Caddy et le domaine cible,
  et distingue explicitement la PWA statique de l'architecture FastAPI actuelle.
- AC7: Les validations incluent build statique, tests unitaires navigateur/local,
  smoke Chromium depuis les fichiers buildés et vérification service worker /
  manifest.
- AC8: Les limites restantes avant adoption produit sont documentées : DBC
  complet, performances gros indexes, persistance durable, compatibilité
  navigateurs et stratégie de migration de l'UI principale.

# Validation
- Run `python3 -m logics_manager lint --require-status`.
- Use `python3 -m logics_manager flow progress task task_020_pwa_statique_deployable_local_first.md --progress <n>%` during multi-wave work.
- Run `python3 -m logics_manager flow finish task task_020_pwa_statique_deployable_local_first.md` after implementation.
- PASSED 2026-07-22: node spikes/pwa-local-engine/build-browser.mjs; node --test spikes/pwa-local-engine/tests/*.test.ts passed 9/9; CTD_ENGINE_ROOT=spikes/pwa-local-engine/site CTD_ENGINE_PORT=9883 CTD_ENGINE_DEBUG_PORT=9233 node spikes/pwa-local-engine/browser-smoke.mjs passed with manifest, active service worker, app-shell cache and workspace save checks.
- Finish workflow executed on 2026-07-22.
- Linked backlog/request close verification passed.

# Report
- Finished on 2026-07-22. The validated local engine is packaged as a static
  deployable PWA with manifest, service worker, app-shell cache, minimal
  workspace lifecycle, quota recovery coverage, Caddy deployment notes and
  documented adoption limits.
- Linked backlog item(s): `item_020_pwa_statique_deployable_local_first`
- Related request(s): `req_010_pwa_statique_deployable_local_first`

# AI Context
- Summary: Task for roadmap milestone 0.3: produce a static installable PWA
  build around the local engine, add service worker/manifest, workspace
  lifecycle, quota handling, deployment docs and browser smoke/PWA validation.
- Keywords: task, pwa, static build, service worker, manifest, workspace, quota,
  caddy, local-first, smoke, deployment
- Use when: Starting or closing the 0.3 static deployable PWA milestone.
- Skip when: Implementing additional ASC/DBC engine parity or the FastAPI server.

# Links
- Request: `req_010_pwa_statique_deployable_local_first`
- Roadmap: `road_001_architecture_pwa_spa_local_first`
- Product brief(s): (none yet)
- Architecture decision(s): (none yet)

# AC Traceability
- request-AC1 -> This task. Proof: PWA static build implemented with deployable site output, no-FastAPI import smoke, manifest/service worker shell cache, workspace save/list/reopen/delete/purge/export/import, quota recovery test, Caddy deployment notes, and documented adoption limits. Source: `spikes/pwa-local-engine/pwa-results-2026-07-22.md`
- request-AC2 -> This task. Proof: PWA static build implemented with deployable site output, no-FastAPI import smoke, manifest/service worker shell cache, workspace save/list/reopen/delete/purge/export/import, quota recovery test, Caddy deployment notes, and documented adoption limits. Source: `spikes/pwa-local-engine/pwa-results-2026-07-22.md`
- request-AC3 -> This task. Proof: PWA static build implemented with deployable site output, no-FastAPI import smoke, manifest/service worker shell cache, workspace save/list/reopen/delete/purge/export/import, quota recovery test, Caddy deployment notes, and documented adoption limits. Source: `spikes/pwa-local-engine/pwa-results-2026-07-22.md`
- request-AC4 -> This task. Proof: PWA static build implemented with deployable site output, no-FastAPI import smoke, manifest/service worker shell cache, workspace save/list/reopen/delete/purge/export/import, quota recovery test, Caddy deployment notes, and documented adoption limits. Source: `spikes/pwa-local-engine/pwa-results-2026-07-22.md`
- request-AC5 -> This task. Proof: PWA static build implemented with deployable site output, no-FastAPI import smoke, manifest/service worker shell cache, workspace save/list/reopen/delete/purge/export/import, quota recovery test, Caddy deployment notes, and documented adoption limits. Source: `spikes/pwa-local-engine/pwa-results-2026-07-22.md`
- request-AC6 -> This task. Proof: PWA static build implemented with deployable site output, no-FastAPI import smoke, manifest/service worker shell cache, workspace save/list/reopen/delete/purge/export/import, quota recovery test, Caddy deployment notes, and documented adoption limits. Source: `spikes/pwa-local-engine/pwa-results-2026-07-22.md`
- request-AC7 -> This task. Proof: PWA static build implemented with deployable site output, no-FastAPI import smoke, manifest/service worker shell cache, workspace save/list/reopen/delete/purge/export/import, quota recovery test, Caddy deployment notes, and documented adoption limits. Source: `spikes/pwa-local-engine/pwa-results-2026-07-22.md`
- request-AC8 -> This task. Proof: PWA static build implemented with deployable site output, no-FastAPI import smoke, manifest/service worker shell cache, workspace save/list/reopen/delete/purge/export/import, quota recovery test, Caddy deployment notes, and documented adoption limits. Source: `spikes/pwa-local-engine/pwa-results-2026-07-22.md`
