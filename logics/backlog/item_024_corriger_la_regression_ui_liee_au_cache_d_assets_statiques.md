## item_024_corriger_la_regression_ui_liee_au_cache_d_assets_statiques - Corriger la regression UI liee au cache d'assets statiques
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: High
> Theme: Operator workflow and runtime integration
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
Apres la modularisation du frontend (task_022, `app.js` -> `js/*.js`) et le
L'operateur doit retrouver ces trois interactions sans avoir a vider

# Scope
- In:
  - one coherent delivery slice from the source request
- Out:
  - unrelated sibling slices that should stay in separate backlog items instead of widening this doc

# Acceptance criteria
- AC1: La reponse de `GET /` reference chaque asset JS/CSS avec un jeton de version
- AC2: La reponse de `GET /` porte un en-tete `Cache-Control` empechant le
- AC3: Un test automatise verifie AC1 (references versionnees + rotation du jeton) et
- AC4: Les trois interactions (redimensionnement des panneaux, repli

# AC Traceability
- request-AC1 -> This backlog slice. Proof: AC1: La reponse de `GET /` reference chaque asset JS/CSS avec un jeton de version
- request-AC2 -> This backlog slice. Proof: AC2: La reponse de `GET /` porte un en-tete `Cache-Control` empechant le
- request-AC3 -> This backlog slice. Proof: AC3: Un test automatise verifie AC1 (references versionnees + rotation du jeton) et
- request-AC4 -> This backlog slice. Proof: AC4: Les trois interactions (redimensionnement des panneaux, repli

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
- Request: `logics/request/req_008_corriger_la_regression_ui_liee_au_cache_d_assets_statiques.md`
- Primary task(s): (none yet)

# AI Context
- Summary: Corriger la regression UI liee au cache d'assets statiques
- Keywords: backlog-groom, request, corriger la regression ui liee au cache d'assets statiques, bounded slice
- Use when: Use when implementing or reviewing the delivery slice for Corriger la regression UI liee au cache d'assets statiques.
- Skip when: Skip when the change is unrelated to this delivery slice or its linked request.

# Priority
- Priority: Medium
- Rationale: Default until groomed.

# Notes
- Hybrid rationale: Derived from request `req_008_corriger_la_regression_ui_liee_au_cache_d_assets_statiques` and kept bounded to one coherent delivery slice.
- Source file: `logics/request/req_008_corriger_la_regression_ui_liee_au_cache_d_assets_statiques.md`.
- Generated locally by logics-manager.
- Task `task_024_corriger_la_regression_ui_liee_au_cache_d_assets_statiques` was finished via `logics-manager flow finish task` on 2026-07-19.

# Tasks
- `task_024_corriger_la_regression_ui_liee_au_cache_d_assets_statiques`
