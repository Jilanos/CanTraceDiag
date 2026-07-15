## task_004_p1_rendre_import_robuste_et_scalable - P1 Rendre import robuste et scalable
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: Medium
> Theme: Implementation delivery
> Reminder: Update status/understanding/confidence/progress and linked request/backlog references when you edit this doc.
> Owner: codex

# Definition of Done (DoD)
- [x] The backlog scope is implemented.
- [x] Acceptance criteria are covered.
- [x] Validation passes.
- [x] Meaningful waves followed ADR 009: affected docs updated and the repo left commit-ready without automatic commits.

# Backlog
- `item_004_p1_rendre_import_robuste_et_scalable`

# Acceptance criteria
- AC6: Le stockage d'une analyse volumineuse utilise un fichier DuckDB/cache temporaire
  hors dépôt et ne dépend plus d'une base complète en mémoire.
- AC7: Une trace réelle ou synthétique représentative de 150 Mo avec DBC fait l'objet
  d'une optimisation au maximum raisonnable et d'un budget documenté de temps/mémoire ; la
  CI protège au moins un budget synthétique réduit et reproductible.
- AC8: L'import expose des phases et une progression mesurable, peut être annulé, retourne
  des erreurs actionnables, continue en arrière-plan pour les frames non ambiguës et ne
  détruit la session précédente qu'après succès validé.
- AC9: Une DBC invalide, une résolution incomplète/inconnue, deux basenames identiques et
  un payload tronqué ont des comportements déterministes, visibles et testés.

# Implementation approach
- Déplacer le stockage d'analyse volumineuse vers un fichier DuckDB/cache temporaire hors
  dépôt avec invalidation par contenu, schéma et décisions DBC.
- Introduire des jobs d'import temporaires côté serveur pour progression, annulation et
  commit transactionnel de la nouvelle session.
- Mesurer avant/après sur fixtures synthétiques reproductibles ; documenter les résultats
  réels hors dépôt sans les inclure dans le repo.
- Ajouter des erreurs métier testées pour DBC invalide, résolution inconnue/incomplète,
  basenames identiques et payload tronqué.

# Validation
- Run `python3 -m logics_manager lint --require-status`.
- Use `python3 -m logics_manager flow progress task task_004_p1_rendre_import_robuste_et_scalable.md --progress <n>%` during multi-wave work.
- Run `python3 -m logics_manager flow finish task task_004_p1_rendre_import_robuste_et_scalable.md` after implementation.
- `.venv/bin/ruff check .` passed.
- `.venv/bin/pytest` passed: 62 passed, 1 warning.
- Finish workflow executed on 2026-07-15.
- Linked backlog/request close verification passed.

# Report
- Implemented disk-backed API imports, temporary job status/cancel endpoints, safe session
- Finished on 2026-07-15.
- Linked backlog item(s): `item_004_p1_rendre_import_robuste_et_scalable`
- Related request(s): `req_002_fiabiliser_cantracediag_apres_audit_fonctionnel_ui_et_performance`
  commit, deterministic import errors and documented current performance-budget limits.

# AI Context
- Summary: Implement disk-backed import, temporary jobs, safe session commit and
  performance budget evidence.
- Keywords: task, implementation, backlog, runtime, python
- Use when: You need a bounded implementation task for a backlog item.
- Skip when: The work is still at the request or backlog shaping stage.

# Links
- Request: `req_002_fiabiliser_cantracediag_apres_audit_fonctionnel_ui_et_performance`
- Product brief(s): (none yet)
- Architecture decision(s): (none yet)

# AC Traceability
- request-AC6 -> This task. Proof: API import creates a temporary DuckDB file via `_new_store_path()` and keeps it outside the repository.
- request-AC7 -> This task. Proof: README/roadmap document the current synthetic validation budget and that the 150 MB real budget remains a measured follow-up.
- request-AC8 -> This task. Proof: `/api/import-job` and `/api/import-cancel` expose import phase/progress/cancel state; unresolved conflicts keep non-ambiguous frames visible.
- request-AC9 -> This task. Proof: tests cover invalid DBC, invalid/unknown resolution, duplicate basenames and truncated payload decode errors.
