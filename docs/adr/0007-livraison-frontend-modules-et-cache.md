# ADR 0007 - Livraison du frontend : modules JS, vues d'espace de travail et cache-busting des assets

## Statut

Accepté

## Contexte

Le frontend a évolué depuis l'`app.js` global initial :

- il est désormais découpé en modules ES par domaine (`web/js/core.js`,
  `import.js`, `signals.js`, `plot.js`, `report.js`, `trace.js`, `inspector.js`,
  `main.js`), chargés en ordre par des balises `<script>` classiques (pas de
  bundler), `core` en premier et `main` en dernier ;
- la navigation par onglets *Analysis / Trace / Report* a été remplacée par un
  contrôle unique de **vues d'espace de travail** : *Plots*, *Plots + trace*
  (vue combinée avec un séparateur redimensionnable), *Trace* et *Report* ;
- les mesures curseur A/B et les statistiques de plage A–B sont fusionnées dans
  un seul tableau de mesure.

Le shell `index.html` est servi dynamiquement par la route `/` (`api.py`) : il y
est lu à chaud et enrichi (jeton de session), il est donc toujours frais. Les
modules JS et la feuille de style sont servis par `StaticFiles` sous `/static/`.

Un incident a révélé une classe de bug propre à ce mode de livraison. Après une
édition des fichiers JS (par exemple la bascule onglets → vues), un navigateur
pouvait apparier un `index.html` **neuf** avec un `main.js` **périmé** issu de sa
fraîcheur de cache heuristique (aucun en-tête `Cache-Control` n'était émis sur
les assets). L'ancien `main.js` référençait un élément supprimé du nouveau HTML
(`presetPlots`) ; l'appel `addEventListener` sur `null` levait une exception qui
interrompait `main.js` avant le câblage des interactions, neutralisant d'un coup
le redimensionnement des panneaux, le repli inspecteur/signaux et les boutons de
vue. Le symptôme se présentait comme une régression de code alors que le code
livré était correct.

## Décision

- **Conserver la livraison sans bundler** : modules ES chargés en ordre, testés
  via la surface explicite `window.__ctd`. Pas de pipeline de build offline pour
  le MVP.
- **Rendre déterministe l'appariement shell ↔ assets par cache-busting** :
  - la route `/` réécrit chaque référence `/static/*.js|*.css` du HTML servi en
    y ajoutant un jeton de version `?v=<token>` ;
  - le jeton (`_asset_version()`) est un condensat court dérivé du nom, de la
    date de modification et de la taille de chaque asset `.js`/`.css`/`.html`,
    de sorte qu'il **change dès qu'un asset change** ;
  - le shell est renvoyé avec `Cache-Control: no-store` : le navigateur ne
    réutilise jamais un HTML stocké et redemande donc les assets versionnés.
- Les assets eux-mêmes restent cacheables : l'URL portant le contenu, un fichier
  modifié obtient une nouvelle URL, ce qui invalide naturellement l'ancienne.

## Alternatives considérées

- **`Cache-Control: no-cache` sur les assets statiques** (revalidation forcée) :
  corrige le symptôme mais dépend d'une revalidation à chaque chargement et ne
  garantit pas l'appariement si un intermédiaire ignore l'en-tête. Le
  versionnement par URL est plus robuste et laisse les assets cacheables.
- **Bundler avec hash de contenu dans le nom de fichier** (Vite/esbuild) :
  standard de l'industrie, mais introduit une étape de build et une dépendance
  d'outillage disproportionnées pour un frontend local sans framework.
- **Ne rien faire / demander un rechargement forcé** : reporte la charge sur
  l'utilisateur à chaque livraison frontend et laisse la régression réapparaître.

## Conséquences

- Un `index.html` frais ne peut plus charger un JS/CSS périmé : la classe de bug
  « HTML neuf + script en cache » est éliminée à la source.
- Chaque édition d'un asset invalide automatiquement son URL côté navigateur,
  sans intervention de l'utilisateur ni vidage manuel du cache.
- Le coût est borné : recalcul d'un condensat sur quelques petits fichiers à
  chaque `GET /`, négligeable pour un serveur local mono-utilisateur.
- Le shell n'est plus mis en cache par le navigateur ; c'est acceptable car il
  est petit, dynamique (jeton + version) et servi en local.
- Non-régression garantie par `tests/test_api.py` : le shell versionne chaque
  asset et interdit son propre cache, et le jeton tourne quand un fichier change.

## Références

- Décision fondatrice : [ADR 0001](0001-application-web-locale.md) (application
  web locale, séparation backend/frontend).
- Identité et composants UI : [ADR 0005](0005-identite-ui-instrument.md),
  `docs/design-ui.md`.
- Implémentation : `src/cantracediag/api.py` (`_asset_version`, route `/`),
  `src/cantracediag/web/`.
- Workflow Logics : `req_008` / `item_024` / `task_024`.
