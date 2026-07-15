## item_001_mvp_analyse_locale_traces_can_asc - Créer le MVP d'analyse locale de traces CAN ASC
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
Deliver a local MVP for offline analysis of CANalyzer ASC traces and local DBC files.
Provide two primary analysis surfaces: stacked signal plots and a configurable trace view.
Keep real traces, DBC files, CANalyzer configs, and generated caches outside Git.

# Scope
- In:
  - one coherent delivery slice from the source request
- Out:
  - unrelated sibling slices that should stay in separate backlog items instead of widening this doc

# Acceptance criteria
- AC1: The user can import a local ASC trace without committing it to the repository.
- AC2: The user can load multiple local DBC files and inspect available messages/signals.
- AC3: The MVP decodes supported frames into physical signal samples while preserving raw frames and decode failures.
- AC4: The graph view displays selected signals as stacked subplots with a shared time axis.
- AC5: Cursor values use the nearest sample; no interpolation is used.
- AC6: The trace view shows raw CAN frames, decoded message names/signals where available, and non-data events.
- AC7: The trace view has a path toward configurable columns: visibility, order, width, and display format.
- AC8: The implementation remains local-first and does not require replay controls.

# AC Traceability
- request-AC1 -> This backlog slice. Proof: AC1: The user can import a local ASC trace without committing it to the repository.
- request-AC2 -> This backlog slice. Proof: AC2: The user can load multiple local DBC files and inspect available messages/signals.
- request-AC3 -> This backlog slice. Proof: AC3: The MVP decodes supported frames into physical signal samples while preserving raw frames and decode failures.
- request-AC4 -> This backlog slice. Proof: AC4: The graph view displays selected signals as stacked subplots with a shared time axis.
- request-AC5 -> This backlog slice. Proof: AC5: Cursor values use the nearest sample; no interpolation is used.
- request-AC6 -> This backlog slice. Proof: AC6: The trace view shows raw CAN frames, decoded message names/signals where available, and non-data events.
- request-AC7 -> This backlog slice. Proof: AC7: The trace view has a path toward configurable columns: visibility, order, width, and display format.
- request-AC8 -> This backlog slice. Proof: AC8: The implementation remains local-first and does not require replay controls.

# Decision framing
- Product framing: Not needed
- Product signals: (none detected)
- Product follow-up: No product brief follow-up is expected based on current signals.
- Architecture framing: Not needed
- Architecture signals: (none detected)
- Architecture follow-up: No architecture decision follow-up is expected based on current signals.

# Links
- Product brief(s): `prod_002_product_brief_cantracediag_mvp`
- Architecture decision(s): `adr_002_adr_architecture_cantracediag_mvp`
- Request: `logics/request/req_000_mvp_analyse_locale_traces_can_asc.md`
- Primary task(s): `task_001_mvp_analyse_locale_traces_can_asc`

# AI Context
- Summary: Créer le MVP d'analyse locale de traces CAN ASC
- Keywords: backlog-groom, request, créer le mvp d'analyse locale de traces can asc, bounded slice
- Use when: Use when implementing or reviewing the delivery slice for Créer le MVP d'analyse locale de traces CAN ASC.
- Skip when: Skip when the change is unrelated to this delivery slice or its linked request.

# Priority
- Priority: High
- Rationale: First P0 slice required before any import, graph, or trace-view implementation can be planned safely.

# Notes
- Hybrid rationale: Derived from request `req_000_mvp_analyse_locale_traces_can_asc` and kept bounded to one coherent delivery slice.
- Source file: `logics/request/req_000_mvp_analyse_locale_traces_can_asc.md`.
- Generated locally by logics-manager.
- Task `task_001_mvp_analyse_locale_traces_can_asc` was finished via `logics-manager flow finish task` on 2026-07-15.

# Tasks
- `task_001_mvp_analyse_locale_traces_can_asc`
