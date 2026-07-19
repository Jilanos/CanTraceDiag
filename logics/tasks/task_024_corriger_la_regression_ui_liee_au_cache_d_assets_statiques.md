## task_024_corriger_la_regression_ui_liee_au_cache_d_assets_statiques - Corriger la regression UI liee au cache d'assets statiques
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: Medium
> Theme: Implementation delivery
> Reminder: Update status/understanding/confidence/progress and linked request/backlog references when you edit this doc.
> Owner: matcha

# Definition of Done (DoD)
- [x] The backlog scope is implemented.
- [x] Acceptance criteria are covered.
- [x] Validation passes.
- [x] Meaningful waves followed ADR 009: affected docs updated and the repo left commit-ready without automatic commits.

# Backlog
- `item_024_corriger_la_regression_ui_liee_au_cache_d_assets_statiques`

# Acceptance criteria
- AC1: La reponse de `GET /` reference chaque asset JS/CSS avec un jeton de version
- AC2: La reponse de `GET /` porte un en-tete `Cache-Control` empechant le
- AC3: Un test automatise verifie AC1 (references versionnees + rotation du jeton) et
- AC4: Les trois interactions (redimensionnement des panneaux, repli

# Validation
- Run `python3 -m logics_manager lint --require-status`.
- Use `python3 -m logics_manager flow progress task task_024_corriger_la_regression_ui_liee_au_cache_d_assets_statiques.md --progress <n>%` during multi-wave work.
- Run `python3 -m logics_manager flow finish task task_024_corriger_la_regression_ui_liee_au_cache_d_assets_statiques.md` after implementation.
- Finish workflow executed on 2026-07-19.
- Linked backlog/request close verification passed.

# Report
- Diagnostic (AC preuve) : le code frontend de codex (workspace views, resizers,
- Finished on 2026-07-19.
- Linked backlog item(s): `item_024_corriger_la_regression_ui_liee_au_cache_d_assets_statiques`
- Related request(s): `req_008_corriger_la_regression_ui_liee_au_cache_d_assets_statiques`
  split) est correct ; un pilotage Playwright en etat neuf montre les trois
  interactions fonctionnelles. La casse provient d'un navigateur servant un
  `index.html` neuf avec un `main.js` PERIME (cache heuristique). L'ancien
  `main.js` executait `$("presetPlots").addEventListener(...)` ; `presetPlots`
  ayant disparu du nouveau HTML, l'appel levait `Cannot read properties of null
  (reading 'addEventListener')`, interrompant `main.js` avant `wireCollapse`,
  `wireSideResize`, `wireSplitResize` et `init()`. Reproduction confirmee par
  interception reseau (nouveau HTML + ancien JS) : les trois symptomes exacts.
- Correctif (AC1, AC2) : `src/cantracediag/api.py` ajoute `_asset_version()` (jeton
  sha1 tronque derive du nom/mtime/taille des assets `.js`/`.css`/`.html`) et
  reecrit dans la route `/` chaque reference `/static/*.js|*.css` en
  `...?v=<jeton>`, avec `Cache-Control: no-store` sur le shell. Un HTML neuf ne
  peut donc plus reference un asset perime : l'URL change avec le contenu.
- Tests (AC3) : `tests/test_api.py` ajoute
  `test_index_versions_bundled_assets_and_forbids_shell_cache` (references
  versionnees + `no-store`) et `test_asset_version_rotates_when_a_bundled_file_changes`
  (rotation du jeton). Tous deux echouent sur le comportement d'avant-correctif.
- Validation (AC4) : suite complete `141 passed` (dont 21 E2E), `ruff check`
  clean. Pilotage navigateur sur l'app corrigee en simulant un cache perime a
  l'URL nue : aucune `pageerror`, boutons de vue OK, repli explorer 264->30,
  resize explorer 264->394 et inspecteur 288->423.

# AI Context
- Summary: Implement corriger la regression ui liee au cache d'assets statiques.
- Keywords: task, implementation, backlog, runtime, python
- Use when: You need a bounded implementation task for a backlog item.
- Skip when: The work is still at the request or backlog shaping stage.

# Links
- Request: `req_008_corriger_la_regression_ui_liee_au_cache_d_assets_statiques`
- Product brief(s): (none yet)
- Architecture decision(s): (none yet)
