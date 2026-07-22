## item_021_migrer_l_ui_produit_vers_la_pwa_local_first_avec_parite_mvp - Migrer l UI produit vers la PWA local-first avec parite MVP
> From version: 1.0.0
> Schema version: 1.0
> Status: In progress
> Understanding: 90%
> Confidence: 85%
> Progress: 45%
> Complexity: High
> Theme: Operator workflow and runtime integration
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
Les jalons 0.1 à 0.3 ont prouvé la faisabilité technique d'une PWA locale, mais
ils ne migrent pas encore le produit. L'interface actuelle reste branchée sur
FastAPI/DuckDB via `/api/...`, tandis que le spike PWA a un rendu minimal et ne
permet pas encore d'affirmer que le MVP fonctionne.

Cette tranche doit migrer le chemin produit restant vers une PWA local-first
avec parité MVP vérifiable, en préservant l'expérience visuelle actuelle et en
prouvant l'absence de dépendance FastAPI pour l'artefact statique.

# Scope
- In:
  - Inventorier les fonctionnalités et endpoints MVP actuels.
  - Introduire une frontière `BackendPort` entre l'UI produit et les opérations
    d'analyse.
  - Porter le rendu principal de `src/cantracediag/web/` vers le build PWA.
  - Remplacer les appels `/api/...` du chemin PWA par `LocalPwaBackend`.
  - Compléter le moteur local pour la parité MVP visible.
  - Remplacer la persistance de trace volumineuse par OPFS/IndexedDB ou une
    stratégie équivalente adaptée aux gros fichiers.
  - Ajouter tests de parité, smoke Chromium MVP et détection d'appels `/api`.
  - Documenter les limites restantes et le signal de retrait/fallback FastAPI.
- Out:
  - Déploiement public réel sur VPS.
  - Suppression immédiate du backend Python de `main`.
  - Parité DBC exhaustive au-delà du MVP validé.
  - Synchronisation cloud, comptes utilisateurs ou workspaces partagés.
  - Optimisations avancées non nécessaires à la preuve MVP.

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

# AC Traceability
- request-AC1 -> This backlog slice. Proof: AC1: Un inventaire exhaustif des fonctionnalités MVP de l'UI actuelle est
- request-AC2 -> This backlog slice. Proof: AC2: Tous les appels `/api/...` utilisés par le MVP sont remplacés dans le
- request-AC3 -> This backlog slice. Proof: AC3: Le rendu principal de l'UI PWA reprend la structure et l'ergonomie de
- request-AC4 -> This backlog slice. Proof: AC4: Le moteur local atteint une parité MVP vérifiée pour import ASC + DBC,
- request-AC5 -> This backlog slice. Proof: AC5: La persistance PWA utilise une stratégie adaptée aux gros fichiers :
- request-AC6 -> This backlog slice. Proof: AC6: Les fichiers ASC possibles jusqu'à 500 Mo sont traités par chunks et/ou
- request-AC7 -> This backlog slice. Proof: AC7: Une suite de tests de parité compare le comportement local PWA au backend
- request-AC8 -> This backlog slice. Proof: AC8: Une smoke Chromium MVP démarre depuis le build statique, désactive ou
- request-AC9 -> This backlog slice. Proof: AC9: Les limites restantes avant déploiement public sont explicitement listées
- request-AC10 -> This backlog slice. Proof: AC10: L'ancienne API FastAPI reste présente comme oracle/fallback pendant la

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
- Request: `req_011_migrer_ui_produit_pwa_local_first_parite_mvp`
- Roadmap: `road_001_architecture_pwa_spa_local_first`
- Primary task(s): `task_021_migrer_l_ui_produit_vers_la_pwa_local_first_avec_parite_mvp`

# AI Context
- Summary: Backlog slice for migrating the current product UI and MVP workflows
  to the static local-first PWA, preserving the existing visual experience and
  replacing FastAPI calls with a browser-local backend behind a port.
- Keywords: backlog-groom, pwa, local-first, product-ui, parity, mvp,
  backend-port, no-fastapi, opfs, indexeddb, smoke
- Use when: Implementing or reviewing the product migration after the 0.1-0.3
  PWA technical spikes.
- Skip when: Only validating the isolated spike UI or maintaining the FastAPI
  local-server path.

# Priority
- Priority: High
- Rationale: This is the gate that decides whether the PWA can be judged as a
  working MVP instead of a technical spike.

# Notes
- Hybrid rationale: Derived from request `req_011_migrer_ui_produit_pwa_local_first_parite_mvp` and kept bounded to one coherent delivery slice.
- Source file: `logics/request/req_011_migrer_ui_produit_pwa_local_first_parite_mvp.md`.
- Generated locally by logics-manager.
- Partial implementation wave 2026-07-22: product UI shell migrated into the
  static PWA build with local backend adapter and no `/api/...` network calls in
  the smoke. The backlog item remains open until worker/chunk import,
  OPFS/IndexedDB persistence, broader parity tests and remaining MVP workflows
  are completed.

# Tasks
- `task_021_migrer_l_ui_produit_vers_la_pwa_local_first_avec_parite_mvp`
