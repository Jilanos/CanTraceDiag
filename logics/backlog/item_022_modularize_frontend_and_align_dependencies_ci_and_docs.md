## item_022_modularize_frontend_and_align_dependencies_ci_and_docs - Modularize frontend and align dependencies CI and docs
> From version: 0.1.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: High
> Theme: Operator workflow and runtime integration
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
Le frontend global et le CSS embarque rendent la refonte finale risquee. Les
dependances, la CI, le virtualenv documente et les documents de statut ne refletent
pas tous l'usage reel. Les fondations doivent etre stabilisees avant la clarte UI.

# Scope
- In:
  - modules core/import/signals/plot/trace/report/inspector et CSS externe
  - surface E2E stable `window.__ctd`
  - usage ou retrait de pyarrow/python-can, code mort et helpers dupliques
  - CI Python 3.11/3.12, budget temps/memoire, environnement et docs techniques alignes
- Out:
  - changements de hierarchie, onglets, langue et presets reserves a `item_023`
  - introduction d'un framework frontend

# Acceptance criteria
- AC15: `app.js` et le CSS embarque sont decoupes par domaines `core`, `import`,
- AC16: `pyarrow` est utilise par l'export Parquet ou retire ; `python-can` est retire
- AC17: Le README, la roadmap, le backlog produit et les documents Logics ne

# AC Traceability
- request-AC15 -> This backlog slice. Proof: AC15: `app.js` et le CSS embarque sont decoupes par domaines `core`, `import`,
- request-AC16 -> This backlog slice. Proof: AC16: `pyarrow` est utilise par l'export Parquet ou retire ; `python-can` est retire
- request-AC17 -> This backlog slice. Proof: AC17: Le README, la roadmap, le backlog produit et les documents Logics ne

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
- Request: `logics/request/req_007_finaliser_workflow_diagnostic_et_clarifier_cantracediag.md`
- Primary task(s): (none yet)

# AI Context
- Summary: Modularize frontend and align dependencies CI and docs
- Keywords: backlog-groom, request, modularize frontend and align dependencies ci and docs, bounded slice
- Use when: Use when implementing or reviewing the delivery slice for Modularize frontend and align dependencies CI and docs.
- Skip when: Skip when the change is unrelated to this delivery slice or its linked request.

# Priority
- Priority: Medium
- Rationale: Cette fondation doit preceder la refonte UI finale mais suit les contrats metier.

# Notes
- Hybrid rationale: Derived from request `req_007_finaliser_workflow_diagnostic_et_clarifier_cantracediag` and kept bounded to one coherent delivery slice.
- Source file: `logics/request/req_007_finaliser_workflow_diagnostic_et_clarifier_cantracediag.md`.
- Generated locally by logics-manager.
- Task `task_022_modularize_frontend_and_align_dependencies_ci_and_docs` was finished via `logics-manager flow finish task` on 2026-07-18.

# Tasks
- `task_022_modularize_frontend_and_align_dependencies_ci_and_docs`
