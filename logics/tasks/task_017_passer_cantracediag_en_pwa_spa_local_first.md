## task_017_passer_cantracediag_en_pwa_spa_local_first - Passer CanTraceDiag en PWA SPA local-first
> From version: 1.0.0
> Schema version: 1.0
> Status: Ready
> Understanding: 90%
> Confidence: 85%
> Progress: 0%
> Complexity: Medium
> Theme: Implementation delivery
> Reminder: Update status/understanding/confidence/progress and linked request/backlog references when you edit this doc.

# Definition of Done (DoD)
- [ ] The backlog scope is implemented.
- [ ] Acceptance criteria are covered.
- [ ] Validation passes.
- [ ] Meaningful waves followed ADR 009: affected docs updated and the repo left commit-ready without automatic commits.

# Backlog
- `item_017_passer_cantracediag_en_pwa_spa_local_first`

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

# Validation
- Run `python3 -m logics_manager lint --require-status`.
- Use `python3 -m logics_manager flow progress task task_017_passer_cantracediag_en_pwa_spa_local_first.md --progress <n>%` during multi-wave work.
- Run `python3 -m logics_manager flow finish task task_017_passer_cantracediag_en_pwa_spa_local_first.md` after implementation.

# Report
- Pending implementation. This task starts with the feasibility spike and should
  only be finished after measured browser evidence is recorded.

# AI Context
- Summary: Implement the first bounded delivery task for the PWA/SPA
  local-first exploration, beginning with a browser-side 500 MB ASC chunking
  spike on branch `feat/pwa-local-first`.
- Keywords: task, pwa, spa, local-first, asc, chunks, 500 mb, worker, browser
  storage, feasibility spike
- Use when: Starting implementation work for the PWA/local-first branch or
  recording measured spike evidence.
- Skip when: Only discussing deployment of the existing FastAPI backend.

# Links
- Request: `req_007_passer_cantracediag_en_pwa_spa_local_first`
- Product brief(s): (none yet)
- Architecture decision(s): (none yet)
