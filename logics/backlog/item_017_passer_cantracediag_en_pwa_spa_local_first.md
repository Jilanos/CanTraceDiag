## item_017_passer_cantracediag_en_pwa_spa_local_first - Passer CanTraceDiag en PWA SPA local-first
> From version: 1.0.0
> Schema version: 1.0
> Status: Ready
> Understanding: 90%
> Confidence: 85%
> Progress: 0%
> Complexity: High
> Theme: Operator workflow and runtime integration
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
CanTraceDiag peut potentiellement devenir une SPA/PWA local-first hébergée
statiquement, mais la faisabilité dépend d'abord de la capacité du navigateur à
gérer des traces ASC volumineuses sans backend Python. Le backlog doit cadrer une
exploration progressive, isolée sur une branche dédiée, avec un premier jalon
bloquant sur la lecture/parsing par chunks de fichiers pouvant atteindre 500 Mo.

# Scope
- In:
  - Créer et utiliser la branche d'exploration `feat/pwa-local-first`.
  - Réaliser un spike navigateur pour lecture chunkée, parsing en Web Worker,
    progression, annulation et observations mémoire sur 50/150/500 Mo.
  - Définir le moteur local cible : stockage browser, index, parser ASC, DBC,
    décodage à la demande et équivalents des endpoints actuels.
  - Documenter le point de décision entre poursuite PWA et pivot serveur
    multi-session.
- Out:
  - Supprimer l'architecture FastAPI/Python actuelle.
  - Promettre la parité complète avant les mesures du spike.
  - Livrer un support mobile pour traces volumineuses.
  - Déployer publiquement une version finale sans backlog/task d'implémentation
    dédiés.

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

# AC Traceability
- request-AC1 -> This backlog slice. Proof: AC1: Une branche dédiée `feat/pwa-local-first` est prévue pour isoler
- request-AC2 -> This backlog slice. Proof: AC2: Un spike navigateur mesure la lecture/parsing par chunks de fichiers ASC
- request-AC3 -> This backlog slice. Proof: AC3: La migration complète est explicitement conditionnée au résultat du spike
- request-AC4 -> This backlog slice. Proof: AC4: Le futur moteur local couvre les responsabilités aujourd'hui portées par
- request-AC5 -> This backlog slice. Proof: AC5: Les workspaces restent isolés par navigateur et stockés localement via
- request-AC6 -> This backlog slice. Proof: AC6: L'architecture actuelle reste disponible comme référence de parité et

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
- Request: `logics/request/req_007_passer_cantracediag_en_pwa_spa_local_first.md`
- Primary task(s): `task_017_passer_cantracediag_en_pwa_spa_local_first`

# AI Context
- Summary: Passer CanTraceDiag en PWA SPA local-first
- Keywords: backlog-groom, request, passer cantracediag en pwa spa local-first, bounded slice
- Use when: Use when implementing or reviewing the delivery slice for Passer CanTraceDiag en PWA SPA local-first.
- Skip when: Skip when the change is unrelated to this delivery slice or its linked request.

# Priority
- Priority: Medium
- Rationale: Important architectural option, but gated by a feasibility spike
  before it should displace active robustness and performance work.

# Notes
- Hybrid rationale: Derived from request `req_007_passer_cantracediag_en_pwa_spa_local_first` and kept bounded to one coherent delivery slice.
- Source file: `logics/request/req_007_passer_cantracediag_en_pwa_spa_local_first.md`.
- Generated locally by logics-manager.

# Tasks
- `task_017_passer_cantracediag_en_pwa_spa_local_first`
