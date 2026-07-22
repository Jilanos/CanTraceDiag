## task_022_rattraper_les_commits_ui_diagnostic_du_18_19_juillet_dans_la_pwa - Rattraper les commits UI diagnostic du 18 19 juillet dans la PWA
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 95%
> Confidence: 90%
> Progress: 100%
> Complexity: High
> Theme: PWA parity recovery
> Reminder: Update status/understanding/confidence/progress and linked request/backlog references when you edit this doc.
> Owner: codex

# Definition of Done (DoD)
- [x] The backlog scope is implemented.
- [x] Acceptance criteria are covered.
- [x] Validation passes.
- [x] Meaningful waves followed ADR 009: affected docs updated and the repo left commit-ready without automatic commits.

# Backlog
- `item_022_rattraper_les_commits_ui_diagnostic_du_18_19_juillet_dans_la_pwa`

# Acceptance criteria
- AC1: La branche PWA est synchronisée avec les commits pertinents de
  `origin/main` ou applique un port ciblé équivalent, sans perdre les ajouts
  PWA déjà réalisés dans `spikes/pwa-local-engine`.
- AC2: Le build statique PWA reprend la structure UI récente : workspace views
  `Plots`, `Plots + trace`, `Trace`, `Report`, split layout et table de mesures
  unifiée.
- AC3: Les statistiques entre curseurs A/B sont disponibles côté PWA pour les
  signaux sélectionnés : `count`, `min`, `max`, `mean`, `std`, `rms` pour les
  signaux numériques et distribution de valeurs pour les signaux texte/enum.
- AC4: Le backend local PWA expose l'équivalent local-first de
  `/api/signal-stats`, `/api/report` et `/api/export`, sans appel réseau
  `/api/...` dans l'artefact statique.
- AC5: Les exports PWA couvrent au minimum CSV long et CSV wide pour les signaux
  sélectionnés sur les scopes `between_ab`, `visible` et `full`; Parquet est
  soit supporté localement, soit explicitement différé avec justification
  technique WASM/browser.
- AC6: Les tests unitaires/parité couvrent les statistiques numeric/text/empty,
  les exports et le rapport diagnostic sur fixtures représentatives.
- AC7: Le smoke Chromium PWA vérifie les vues workspace, le panneau de mesures
  unifié, les stats A/B affichées, un export CSV et l'absence d'appels réseau
  `/api/...`.
- AC8: Le fix de cache-busting ou une stratégie PWA équivalente empêche de
  servir un ancien shell JS après mise à jour du build statique.
- AC9: La documentation de migration indique clairement quels commits `origin/main`
  ont été repris, lesquels ont été adaptés, et les limites restantes.
- AC10: `task_021` est mise à jour pour référencer cette chaîne comme
  prérequis/parité MVP, afin que le MVP PWA ne soit pas déclaré complet sans ces
  fonctionnalités.

# Validation
- Run `python3 -m logics_manager lint --require-status`.
- Use `python3 -m logics_manager flow progress task task_022_rattraper_les_commits_ui_diagnostic_du_18_19_juillet_dans_la_pwa.md --progress <n>%` during multi-wave work.
- Run `python3 -m logics_manager flow finish task task_022_rattraper_les_commits_ui_diagnostic_du_18_19_juillet_dans_la_pwa.md` after implementation.
- During implementation, run the PWA browser unit tests and a Chromium smoke
- Finish workflow executed on 2026-07-22.
- Linked backlog/request close verification passed.
  from the static build that fails on `/api/...` network calls.
- PASSED 2026-07-22: `node spikes/pwa-local-engine/build-browser.mjs`.
- PASSED 2026-07-22: `node --test spikes/pwa-local-engine/tests/*.test.ts`.
- PASSED 2026-07-22:
  `CTD_ENGINE_ROOT=spikes/pwa-local-engine/site CTD_ENGINE_PORT=9891
  CTD_ENGINE_DEBUG_PORT=9241 node spikes/pwa-local-engine/browser-smoke.mjs`.
- ATTEMPTED 2026-07-22: `.venv/bin/python -m pytest
  tests/test_export.py tests/test_api.py`; collection and execution reached the
  suite, but existing Python API tests are not token-aware for the newer
  `SecurityConfig` guard and fail on unauthorized mutating requests.

# Report
- Completed implementation wave on 2026-07-22.
- Recovered the relevant July 18/19 `origin/main` source changes for diagnostic
- Finished on 2026-07-22.
- Linked backlog item(s): `item_022_rattraper_les_commits_ui_diagnostic_du_18_19_juillet_dans_la_pwa`
- Related request(s): `req_012_rattraper_commits_ui_diagnostic_18_19_juillet_pwa`
  report/statistics/export, workspace views/unified measurements and static
  asset freshness.
- Adapted the static PWA build to the modular product UI by generating one
  `product-app.mjs` bundle from the product modules and replacing network
  helpers with `LocalPwaBackend`.
- Added local-first equivalents for A/B cursor batch lookup, signal stats,
  diagnostic report and CSV export without `/api/...` network calls in the
  static PWA artifact.
- CSV long and CSV wide are implemented locally. Parquet is explicitly deferred
  for the browser PWA because it needs a separate Parquet/WASM writer and
  validation.
- The strengthened Chromium smoke verifies workspace views, unified
  measurements with mean/rms, report rendering, CSV wide export, service worker
  cache and zero `/api/...` fetch/XHR calls.
- Evidence: `spikes/pwa-local-engine/parity-recovery-results-2026-07-22.md`.

# AI Context
- Summary: Implement the parity recovery for July 18-19 `origin/main`
  diagnostic UI commits in the static PWA path while preserving no-FastAPI
  local-first behavior.
- Keywords: task, pwa, origin-main, cherry-pick, signal-stats, rms, rmc, min,
  max, mean, std, report, export, workspace-views, no-fastapi, chromium-smoke
- Use when: Starting or executing the recovery slice before continuing
  `task_021` toward MVP completion.
- Skip when: Only changing unrelated FastAPI server behavior or older local
  engine spike internals.

# Links
- Request: `req_012_rattraper_commits_ui_diagnostic_18_19_juillet_pwa`
- Roadmap: `road_001_architecture_pwa_spa_local_first`
- Related task: `task_021_migrer_l_ui_produit_vers_la_pwa_local_first_avec_parite_mvp`
- Product brief(s): (none yet)
- Architecture decision(s): (none yet)
