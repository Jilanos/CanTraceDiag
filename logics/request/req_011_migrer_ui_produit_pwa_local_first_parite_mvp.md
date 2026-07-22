## req_011_migrer_ui_produit_pwa_local_first_parite_mvp - Migrer l UI produit vers la PWA local-first avec parite MVP
> From version: 1.0.0
> Schema version: 1.0
> Status: Draft
> Understanding: 90
> Confidence: 80
> Complexity: High
> Theme: Product migration
> Reminder: Update status/understanding/confidence and linked backlog/task references when you edit this doc.

# Needs
- Migrer le reste des fonctionnalités de l'application actuelle vers la PWA
  local-first sans perdre le rendu produit existant ni les workflows MVP.
- Remplacer progressivement les appels `/api/...` de l'UI actuelle par un
  backend local navigateur, avec une preuve de parité fonctionnelle avant de
  considérer l'ancienne API FastAPI comme débranchable.
- Produire un résultat vérifiable par l'utilisateur : même expérience visuelle
  principale, import local ASC + DBC, résolution DBC, bibliothèque/workspaces,
  exploration trace, signaux, séries, curseur, export et purge, le tout sans
  serveur Python pour le chemin PWA.

# Context
- Les jalons 0.1, 0.2 et 0.3 ont prouvé des briques techniques : lecture
  chunkée 500 MiB, moteur local ASC/DBC fixture-focused, build statique PWA,
  service worker et workspaces minimaux.
- Ces jalons ne migrent pas encore le produit. L'UI actuelle reste dans
  `src/cantracediag/web/`, avec des appels `/api/...` vers FastAPI et DuckDB
  côté Python.
- Le spike PWA dans `spikes/pwa-local-engine/` a un rendu minimal qui ne doit
  pas être considéré comme cible produit. La migration doit reprendre le rendu
  et l'ergonomie de l'interface actuelle, puis substituer le backend derrière
  une frontière explicite.
- En l'état actuel, il est difficile de dire si le MVP PWA fonctionne réellement
  parce que la preuve couvre surtout des fixtures et une UI technique. Cette
  chaîne doit donc commencer par un inventaire de parité et finir par une smoke
  MVP complète.

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

# Definition of Ready (DoR)
- [x] Problem statement is explicit and user impact is clear.
- [x] Scope boundaries (in/out) are explicit.
- [x] Acceptance criteria are testable.
- [x] Dependencies and known risks are listed.

# Companion docs
- Product brief(s): (none yet)
- Architecture decision(s): (none yet)

# References
- `logics/roadmap/road_001_architecture_pwa_spa_local_first.md`
- `spikes/pwa-500mb/results-2026-07-22.md`
- `spikes/pwa-local-engine/results-2026-07-22.md`
- `spikes/pwa-local-engine/pwa-results-2026-07-22.md`
- `src/cantracediag/web/app.js`
- `src/cantracediag/web/index.html`
- `src/cantracediag/api.py`
- `src/cantracediag/store.py`

# AI Context
- Summary: Request to migrate the remaining product UI and MVP workflows from
  the FastAPI-backed app to the static local-first PWA, preserving the current
  visual/product experience and proving no-FastAPI parity before claiming the
  MVP works.
- Keywords: request-draft, pwa, spa, local-first, product migration, parity,
  mvp, backend-port, no-fastapi, opfs, indexeddb, ui-migration
- Use when: Planning or executing the product migration after the 0.1-0.3 PWA
  technical spikes.
- Skip when: Only validating the isolated spike UI or deploying the existing
  FastAPI local-server app.

# Backlog
- `item_021_migrer_l_ui_produit_vers_la_pwa_local_first_avec_parite_mvp`
