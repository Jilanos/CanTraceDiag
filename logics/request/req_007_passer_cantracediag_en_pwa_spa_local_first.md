## req_007_passer_cantracediag_en_pwa_spa_local_first - Passer CanTraceDiag en PWA SPA local-first
> From version: 1.0.0
> Schema version: 1.0
> Status: Draft
> Understanding: 90%
> Confidence: 85%
> Complexity: Medium
> Theme: General
> Reminder: Update status/understanding/confidence and linked backlog/task references when you edit this doc.

# Needs
- Explorer une nouvelle architecture CanTraceDiag en SPA/PWA local-first sur une
  branche dédiée, afin que l'outil puisse être hébergé comme fichiers statiques
  tout en gardant les traces, DBC, index, caches et workspaces dans le navigateur
  de chaque utilisateur.
- Vérifier d'abord la faisabilité technique sur des fichiers ASC volumineux
  pouvant atteindre 500 Mo, car cette contrainte détermine si une migration
  complète hors backend Python est raisonnable.
- Conserver l'architecture FastAPI/Python actuelle comme référence tant que le
  moteur navigateur n'a pas prouvé sa parité fonctionnelle et ses performances.

# Context
- Le modèle actuel est une web UI servie par FastAPI avec une session backend
  unique et un index DuckDB côté Python. Il est efficace pour les gros fichiers,
  mais ce n'est pas le même modèle qu'une application statique local-first où
  chaque navigateur porte son propre workspace.
- Le modèle recherché est proche d'une SPA/PWA hébergée statiquement : le serveur
  ne sert que `index.html`, JavaScript, CSS et assets ; l'import, le parsing, le
  stockage et la reprise se font côté navigateur.
- La contrainte principale est la taille potentielle des traces. Un fichier texte
  ASC de 500 Mo ne doit jamais être converti en millions d'objets JavaScript
  retenus en mémoire. La migration doit donc commencer par une lecture chunkée,
  un parsing en Web Worker et un stockage batché.
- La roadmap liée `road_001_architecture_pwa_spa_local_first` détaille le
  séquençage proposé : spike 500 Mo, moteur local ASC/DBC, puis PWA statique
  déployable.

# Acceptance criteria
- AC1: Une branche dédiée `feat/pwa-local-first` est prévue pour isoler
  l'exploration de l'architecture actuelle.
- AC2: Un spike navigateur mesure la lecture/parsing par chunks de fichiers ASC
  jusqu'à 500 Mo avec UI non bloquée, progression, annulation et observations de
  mémoire.
- AC3: La migration complète est explicitement conditionnée au résultat du spike
  500 Mo ; un échec doit orienter vers une architecture serveur multi-session
  plutôt qu'une réécriture PWA.
- AC4: Le futur moteur local couvre les responsabilités aujourd'hui portées par
  les endpoints `/api/status`, `/api/signals`, `/api/series`, `/api/trace`,
  `/api/cursor`, `/api/frame-signals`, import job et purge.
- AC5: Les workspaces restent isolés par navigateur et stockés localement via
  OPFS, IndexedDB, DuckDB-WASM ou une combinaison justifiée par benchmarks.
- AC6: L'architecture actuelle reste disponible comme référence de parité et
  comme fallback jusqu'à validation de la PWA.

# Definition of Ready (DoR)
- [x] Problem statement is explicit and user impact is clear.
- [x] Scope boundaries (in/out) are explicit.
- [x] Acceptance criteria are testable.
- [x] Dependencies and known risks are listed.

# Companion docs
- Product brief(s): (none yet)
- Architecture decision(s): (none yet)
- Roadmap(s): `road_001_architecture_pwa_spa_local_first`

# References
- `logics/roadmap/road_001_architecture_pwa_spa_local_first.md`
- `src/cantracediag/api.py`
- `src/cantracediag/pipeline.py`
- `src/cantracediag/formats/asc.py`
- `src/cantracediag/store.py`

# AI Context
- Summary: Request to explore a dedicated PWA/SPA local-first migration branch
  for CanTraceDiag, gated by browser-side chunked handling of possible 500 MB
  ASC files.
- Keywords: request-draft, pwa, spa, local-first, asc, dbc, chunks, 500 mb,
  browser storage, opfs, indexeddb, duckdb-wasm
- Use when: Creating backlog slices for the PWA/local-first exploration or
  reviewing whether the roadmap should proceed after the browser spike.
- Skip when: Working on the current FastAPI backend deployment path or local WSL
  launcher workflow.

# Backlog
- `item_017_passer_cantracediag_en_pwa_spa_local_first`
