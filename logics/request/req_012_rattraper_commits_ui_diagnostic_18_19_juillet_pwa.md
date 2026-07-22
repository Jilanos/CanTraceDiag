## req_012_rattraper_commits_ui_diagnostic_18_19_juillet_pwa - Rattraper les commits UI diagnostic du 18 19 juillet dans la PWA
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 95
> Confidence: 90
> Complexity: High
> Theme: PWA parity recovery
> Reminder: Update status/understanding/confidence and linked backlog/task references when you edit this doc.

# Needs
- Rattraper dans la branche PWA les fonctionnalités présentes dans
  `origin/main` depuis les commits du 18/19 juillet 2026, en particulier les
  statistiques de signaux entre curseurs A/B, les mesures unifiées, le rapport
  diagnostic, les exports et les vues workspace.
- Empêcher la migration PWA de se baser sur une ancienne version de l'UI produit
  qui ne contient pas ces fonctionnalités récentes.
- Reprendre ces fonctionnalités dans le chemin local-first sans réintroduire une
  dépendance FastAPI pour l'artefact statique PWA.

# Context
- Un `git fetch --all --prune` a ramené les commits récents sur `origin/main`.
- Les commits sources identifiés sont :
  - `7a83002` du 18 juillet 2026 :
    `feat(diagnostic): add report statistics and exports`.
  - `84ac5c0` du 19 juillet 2026 :
    `feat(ui): workspace views with split layout and unified measurements`.
  - `57b9fb1` du 19 juillet 2026 :
    `fix(web): cache-bust static assets so a fresh shell never loads stale JS`.
- Les fonctionnalités manquantes côté PWA incluent :
  - `/api/signal-stats` et les stats `count/min/max/mean/std/rms` entre A/B.
  - la table de mesures unifiée cursor values + range analysis.
  - les vues workspace `Plots`, `Plots + trace`, `Trace`, `Report`.
  - le rapport diagnostic.
  - les exports CSV long, CSV wide et Parquet.
  - les tests associés de stats/export/report et les e2e UI.
- La task PWA en cours `task_021_migrer_l_ui_produit_vers_la_pwa_local_first_avec_parite_mvp`
  doit rester ouverte tant que ce rattrapage n'est pas intégré ou explicitement
  deferre.

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
  soit supporté localement, soit explicitement deferre avec justification
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

# Definition of Ready (DoR)
- [x] Problem statement is explicit and user impact is clear.
- [x] Scope boundaries (in/out) are explicit.
- [x] Acceptance criteria are testable.
- [x] Dependencies and known risks are listed.

# AC Traceability
- AC1 -> `task_022_rattraper_les_commits_ui_diagnostic_du_18_19_juillet_dans_la_pwa`. Proof: relevant `origin/main` commits `7a83002`, `84ac5c0` and `57b9fb1` were recovered or adapted in the branch while preserving `spikes/pwa-local-engine`; see `spikes/pwa-local-engine/parity-recovery-results-2026-07-22.md`.
- AC2 -> `task_022_rattraper_les_commits_ui_diagnostic_du_18_19_juillet_dans_la_pwa`. Proof: Chromium smoke passed with workspace views and split layout from the static PWA build; see `spikes/pwa-local-engine/parity-recovery-results-2026-07-22.md`.
- AC3 -> `task_022_rattraper_les_commits_ui_diagnostic_du_18_19_juillet_dans_la_pwa`. Proof: local stats cover numeric `count`, `min`, `max`, `mean`, `std`, `rms` and text distribution payloads; node tests passed.
- AC4 -> `task_022_rattraper_les_commits_ui_diagnostic_du_18_19_juillet_dans_la_pwa`. Proof: `LocalPwaBackend` exposes local equivalents for cursors, signal stats, report and export; smoke observed zero `/api/...` fetch/XHR calls.
- AC5 -> `task_022_rattraper_les_commits_ui_diagnostic_du_18_19_juillet_dans_la_pwa`. Proof: CSV long and CSV wide are implemented locally; Parquet is explicitly deferred with browser/WASM rationale in `spikes/pwa-local-engine/parity-recovery-results-2026-07-22.md`.
- AC6 -> `task_022_rattraper_les_commits_ui_diagnostic_du_18_19_juillet_dans_la_pwa`. Proof: `node --test spikes/pwa-local-engine/tests/*.test.ts` passed and covers stats, report and export behavior on fixtures.
- AC7 -> `task_022_rattraper_les_commits_ui_diagnostic_du_18_19_juillet_dans_la_pwa`. Proof: Chromium smoke passed for workspace views, unified measurement table, mean/rms stats, report, CSV export and zero `/api/...` network calls.
- AC8 -> `task_022_rattraper_les_commits_ui_diagnostic_du_18_19_juillet_dans_la_pwa`. Proof: static shell cache includes the generated product app and product CSS; source cache-busting commit was recovered for the FastAPI fallback path.
- AC9 -> `task_022_rattraper_les_commits_ui_diagnostic_du_18_19_juillet_dans_la_pwa`. Proof: migration results are documented in `spikes/pwa-local-engine/parity-recovery-results-2026-07-22.md`.
- AC10 -> `task_022_rattraper_les_commits_ui_diagnostic_du_18_19_juillet_dans_la_pwa`. Proof: `task_021_migrer_l_ui_produit_vers_la_pwa_local_first_avec_parite_mvp` now records that `task_022` completed the recovery prerequisite.

# Companion docs
- Product brief(s): (none yet)
- Architecture decision(s): (none yet)

# References
- `7a83002`
- `84ac5c0`
- `57b9fb1`
- `origin/main`
- `logics/tasks/task_021_migrer_l_ui_produit_vers_la_pwa_local_first_avec_parite_mvp.md`
- `logics/roadmap/road_001_architecture_pwa_spa_local_first.md`
- `src/cantracediag/api.py`
- `src/cantracediag/export.py`
- `src/cantracediag/store.py`
- `src/cantracediag/web/index.html`
- `src/cantracediag/web/app.js`
- `src/cantracediag/web/js/plot.js`
- `src/cantracediag/web/js/report.js`
- `spikes/pwa-local-engine/src/product-backend.ts`
- `spikes/pwa-local-engine/src/local-backend.ts`

# AI Context
- Summary: Request to recover the July 18-19 `origin/main` diagnostic UI
  features into the PWA migration: A/B range statistics, unified measurements,
  report, exports, workspace views and cache freshness, while preserving the
  no-FastAPI static PWA path.
- Keywords: request-draft, pwa, origin-main, rebase, cherry-pick, signal-stats,
  rms, rmc, min, max, mean, std, export, report, workspace-views, no-fastapi
- Use when: Planning or executing the parity recovery before continuing
  `task_021` toward MVP completion.
- Skip when: Only working on the older minimal PWA spike or unrelated FastAPI
  maintenance.

# Backlog
- `item_022_rattraper_les_commits_ui_diagnostic_du_18_19_juillet_dans_la_pwa`
