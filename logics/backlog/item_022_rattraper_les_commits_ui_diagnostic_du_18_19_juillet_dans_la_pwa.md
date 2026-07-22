## item_022_rattraper_les_commits_ui_diagnostic_du_18_19_juillet_dans_la_pwa - Rattraper les commits UI diagnostic du 18 19 juillet dans la PWA
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 95%
> Confidence: 90%
> Progress: 100%
> Complexity: High
> Theme: PWA parity recovery
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
La branche PWA a ete construite depuis une base UI qui ne contient pas encore
les commits produit recents du 18/19 juillet 2026 presents sur `origin/main`.
Sans rattrapage, le MVP PWA donne un rendu et un comportement en retard par
rapport a l'outil actuel : statistiques entre curseurs A/B, mesures unifiees,
rapport diagnostic, exports et vues workspace manquent ou ne sont pas integres.

Le rattrapage doit reprendre ces fonctionnalites dans le chemin local-first
sans reintroduire une dependance FastAPI pour l'artefact statique PWA.

# Scope
- In:
  - Comparer la branche PWA actuelle avec `origin/main` et les commits sources
    `7a83002`, `84ac5c0` et `57b9fb1`.
  - Choisir une strategie de merge, rebase, cherry-pick ou port cible qui
    preserve les ajouts PWA deja realises dans `spikes/pwa-local-engine`.
  - Porter dans le build statique PWA les vues workspace, le split layout et la
    table de mesures unifiee.
  - Implementer les equivalents local-first des stats A/B, du rapport et des
    exports sans appels reseau `/api/...`.
  - Couvrir au minimum les exports CSV long et CSV wide; documenter clairement
    si Parquet est reporte pour contrainte navigateur/WASM.
  - Ajouter ou adapter les tests et le smoke Chromium PWA.
  - Mettre a jour la documentation de migration et `task_021`.
- Out:
  - Supprimer l'ancienne API FastAPI de `main`.
  - Deployer publiquement sur le VPS ou `paulmondou.fr`.
  - Ajouter des workspaces partages ou une base serveur multi-utilisateur.
  - Completer toute la parite DBC hors des fonctionnalites necessaires a cette
    tranche.

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

# AC Traceability
- request-AC1 -> This backlog slice. Proof: sync or targeted port from `origin/main` keeps existing PWA work.
- request-AC2 -> This backlog slice. Proof: recent workspace views and unified measurements are present in the static PWA build.
- request-AC3 -> This backlog slice. Proof: A/B stats include numeric metrics and text distributions.
- request-AC4 -> This backlog slice. Proof: local-first equivalents replace `/api/signal-stats`, `/api/report` and `/api/export`.
- request-AC5 -> This backlog slice. Proof: CSV long/wide exports work; Parquet is supported or explicitly deferred.
- request-AC6 -> This backlog slice. Proof: stats, export and report tests cover representative fixtures.
- request-AC7 -> This backlog slice. Proof: Chromium smoke checks UI parity and no `/api/...` calls.
- request-AC8 -> This backlog slice. Proof: cache freshness strategy prevents stale app shell reuse.
- request-AC9 -> This backlog slice. Proof: migration doc names recovered/adapted commits and remaining limits.
- request-AC10 -> This backlog slice. Proof: `task_021` references this chain as a prerequisite before MVP completion.

# Decision framing
- Product framing: Not needed
- Product signals: (none detected)
- Product follow-up: No product brief follow-up is expected based on current signals.
- Architecture framing: Not needed
- Architecture signals: (none detected)
- Architecture follow-up: No architecture decision follow-up is expected based on current signals.

# Links
- Product brief(s): (none yet)
- Architecture decision(s): (none yet)
- Request: `req_012_rattraper_commits_ui_diagnostic_18_19_juillet_pwa`
- Roadmap: `road_001_architecture_pwa_spa_local_first`
- Primary task(s): `task_022_rattraper_les_commits_ui_diagnostic_du_18_19_juillet_dans_la_pwa`

# AI Context
- Summary: Recover the July 18-19 `origin/main` diagnostic UI features into
  the PWA migration without bringing FastAPI network calls back into the static
  local-first artifact.
- Keywords: backlog, pwa, origin-main, cherry-pick, rebase, signal-stats, rms,
  rmc, min, max, mean, std, export, report, workspace-views, no-fastapi
- Use when: Implementing or reviewing the parity recovery before continuing
  `task_021` toward MVP completion.
- Skip when: Working only on unrelated FastAPI maintenance or the old minimal
  PWA spike.

# Priority
- Priority: High
- Rationale: Blocks a credible MVP parity judgement for the PWA migration.

# Notes
- Hybrid rationale: Derived from request `req_012_rattraper_commits_ui_diagnostic_18_19_juillet_pwa` and kept bounded to one coherent delivery slice.
- Source file: `logics/request/req_012_rattraper_commits_ui_diagnostic_18_19_juillet_pwa.md`.
- Source commits:
  - `7a83002` - `feat(diagnostic): add report statistics and exports`.
  - `84ac5c0` - `feat(ui): workspace views with split layout and unified measurements`.
  - `57b9fb1` - `fix(web): cache-bust static assets so a fresh shell never loads stale JS`.
- Generated locally by logics-manager.
- Task `task_022_rattraper_les_commits_ui_diagnostic_du_18_19_juillet_dans_la_pwa` was finished via `logics-manager flow finish task` on 2026-07-22.

# Tasks
- `task_022_rattraper_les_commits_ui_diagnostic_du_18_19_juillet_dans_la_pwa`
