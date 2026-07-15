## task_005_p1_completer_le_workflow_diagnostic - P1 Completer le workflow diagnostic
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
- `item_005_p1_completer_le_workflow_diagnostic`

# Acceptance criteria
- AC10: La vue trace filtre côté serveur par signal en combinaison avec temps, ID, message,
  direction, statut et événement.
- AC11: La recherche de signaux couvre message, signal, ID, unité et DBC, et permet de
  distinguer les signaux présents dans la trace et ceux issus de la DBC retenue.
- AC12: Les colonnes pertinentes proposent les formats attendus (temps, hexadécimal,
  décimal, binaire), une largeur réellement maîtrisée et une persistance testée.

# Implementation approach
- Étendre les endpoints de trace pour filtrer par signal en combinaison avec les filtres
  existants.
- Étendre l'index ou les structures de recherche signal pour couvrir message, signal, ID,
  unité et DBC.
- Exposer clairement dans l'UI les signaux réellement présents dans la trace et ceux
  disponibles seulement via la DBC retenue.
- Ajouter les formats de colonnes attendus et tester leur persistance.
- Inclure dans le rapport d'import les décisions DBC et anomalies consommables par
  l'inspecteur.

# Validation
- Run `python3 -m logics_manager lint --require-status`.
- Use `python3 -m logics_manager flow progress task task_005_p1_completer_le_workflow_diagnostic.md --progress <n>%` during multi-wave work.
- Run `python3 -m logics_manager flow finish task task_005_p1_completer_le_workflow_diagnostic.md` after implementation.
- `.venv/bin/ruff check .` passed.
- `.venv/bin/pytest` passed: 62 passed, 1 warning.
- Finish workflow executed on 2026-07-15.
- Linked backlog/request close verification passed.

# Report
- Implemented server-side signal filtering, broader signal search, present/DBC distinction
- Finished on 2026-07-15.
- Linked backlog item(s): `item_005_p1_completer_le_workflow_diagnostic`
- Related request(s): `req_002_fiabiliser_cantracediag_apres_audit_fonctionnel_ui_et_performance`
  and ID/DLC/data column formats.

# AI Context
- Summary: Implement server-side signal filters, broader signal search, column formats and
  import report completion.
- Keywords: task, implementation, backlog, runtime, python
- Use when: You need a bounded implementation task for a backlog item.
- Skip when: The work is still at the request or backlog shaping stage.

# Links
- Request: `req_002_fiabiliser_cantracediag_apres_audit_fonctionnel_ui_et_performance`
- Product brief(s): (none yet)
- Architecture decision(s): (none yet)

# AC Traceability
- request-AC10 -> This task. Proof: `TraceStore.trace_rows()` and `/api/trace` accept `signal` combined with time, ID, message, direction, status and event filters.
- request-AC11 -> This task. Proof: signal explorer search covers message, signal, ID, unit and DBC; `/api/signals` returns `present`.
- request-AC12 -> This task. Proof: ID/DLC/data columns support hex/dec/bin/text formats with persisted column settings.
