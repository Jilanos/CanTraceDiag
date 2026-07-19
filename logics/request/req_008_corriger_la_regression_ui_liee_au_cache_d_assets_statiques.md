## req_008_corriger_la_regression_ui_liee_au_cache_d_assets_statiques - Corriger la regression UI liee au cache d'assets statiques
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 100
> Confidence: 95
> Complexity: medium
> Theme: ui-asset-cache-busting
> Reminder: Update status/understanding/confidence and linked backlog/task references when you edit this doc.

# Needs
- Apres la modularisation du frontend (task_022, `app.js` -> `js/*.js`) et le
  passage aux "workspace views" (remplacement des onglets), l'operateur observe
  trois regressions simultanees : le redimensionnement des panneaux lateraux, le
  repli de l'inspecteur et des signaux, et les boutons de changement de vue ne
  repondent plus.
- L'operateur doit retrouver ces trois interactions sans avoir a vider
  manuellement le cache de son navigateur a chaque livraison frontend.

# Context
- Diagnostic reproduit le 19 juillet 2026 sur `main` (modifications de travail non
  commitees). Les 21 tests E2E existants passent et un pilotage Playwright en etat
  neuf montre que les trois interactions fonctionnent correctement avec le code
  actuel : le code livre n'est pas fautif en soi.
- Cause racine prouvee par interception reseau : lorsque le navigateur sert un
  `index.html` neuf mais un `main.js` PERIME depuis son cache heuristique,
  l'ancien `main.js` execute `$("presetPlots").addEventListener(...)`. Or le bouton
  `presetPlots` n'existe plus dans le nouveau HTML, donc l'appel leve
  `Cannot read properties of null (reading 'addEventListener')`. Cette exception
  interrompt le module `main.js` avant `wireCollapse`, `wireSideResize`,
  `wireSplitResize` et `init()`, ce qui neutralise exactement les trois fonctions
  signalees.
- `index.html` est servi dynamiquement (`api.py`, route `/`, `read_text`) donc
  toujours frais ; les assets `/static/js/*.js` et `/static/styles.css` sont servis
  par `StaticFiles` sans en-tete `Cache-Control`, laissant le navigateur appliquer
  une fraicheur heuristique et servir un JS perime apres une edition.
- Il s'agit d'une classe de bug recurrente : chaque edition d'un fichier JS/CSS
  peut casser l'UI jusqu'a un rechargement force, tant que les URL d'assets ne
  changent pas avec leur contenu.

# Product decisions
- Le code frontend de codex (views + resizers + split) est conserve tel quel : il
  est correct. La correction porte uniquement sur la livraison des assets.
- Adopter un cache-busting deterministe : versionner les URL d'assets servies dans
  `index.html` avec un jeton derive du contenu des fichiers, et empecher la mise en
  cache du shell HTML, afin qu'un HTML neuf ne puisse jamais reference un JS/CSS
  perime.

# Scope
- In: versionnement des references `/static/*.js|*.css` dans le HTML servi, en-tetes
  de cache du shell, test de non-regression cote API, revalidation E2E des trois
  interactions.
- Out: toute refonte du JS des vues/resizers (non fautif), gestion d'un pipeline de
  build/hash offline, service worker.

# Acceptance criteria
- AC1: La reponse de `GET /` reference chaque asset JS/CSS avec un jeton de version
  (`?v=<token>`) et le jeton change quand un fichier d'asset change.
- AC2: La reponse de `GET /` porte un en-tete `Cache-Control` empechant le
  navigateur de conserver un shell perime (`no-cache`/`no-store`).
- AC3: Un test automatise verifie AC1 (references versionnees + rotation du jeton) et
  AC2, et echouerait sur le comportement d'avant-correctif.
- AC4: Les trois interactions (redimensionnement des panneaux, repli
  inspecteur/signaux, boutons de vue) sont revalidees fonctionnelles via pilotage
  navigateur, et la suite E2E existante reste verte.

# Definition of Ready (DoR)
- [ ] Problem statement is explicit and user impact is clear.
- [ ] Scope boundaries (in/out) are explicit.
- [ ] Acceptance criteria are testable.
- [ ] Dependencies and known risks are listed.

# Companion docs
- Product brief(s): (none yet)
- Architecture decision(s): (none yet)

# References
- `logics_manager/flow.py`
- `logics_manager/assist.py`
- `tests/python/test_logics_manager_cli.py`

# AI Context
- Summary: Draft a bounded request for corriger la regression ui liee au cache d'assets statiques.
- Keywords: request-draft, logics-manager, python runtime, bundled CLI
- Use when: You need a new bounded request doc for the Logics workflow.
- Skip when: The work already has an existing request or should go straight to a backlog slice.

# Backlog
- none
- `item_024_corriger_la_regression_ui_liee_au_cache_d_assets_statiques`
