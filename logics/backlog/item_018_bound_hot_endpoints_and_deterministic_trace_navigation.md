## item_018_bound_hot_endpoints_and_deterministic_trace_navigation - Bound hot endpoints and deterministic trace navigation
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
Les recherches de curseur et de localisation peuvent scanner une serie ou une trace
complete. La pagination `OFFSET` trie seulement par timestamp et recalcule le total,
ce qui rend le cout et l'ordre fragiles sur les acquisitions volumineuses.

# Scope
- In:
  - recherche bornee avant/apres un timestamp et endpoint curseur batch A/B
  - ordre canonique `(timestamp_s, seq)` et pagination par curseur opaque
  - total exact mis en cache apres chaque changement de filtres
  - coherence de `trace-locate` et benchmark synthétique anti-regression
- Out:
  - refonte visuelle de la trace et des filtres
  - chargement complet d'une acquisition dans le navigateur

# Acceptance criteria
- AC8: La recherche du point le plus proche utilise au plus une requete bornee avant
- AC9: La trace est ordonnee par `(timestamp_s, seq)` et paginee par curseur opaque.

# AC Traceability
- request-AC8 -> This backlog slice. Proof: AC8: La recherche du point le plus proche utilise au plus une requete bornee avant
- request-AC9 -> This backlog slice. Proof: AC9: La trace est ordonnee par `(timestamp_s, seq)` et paginee par curseur opaque.

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
- Summary: Bound hot endpoints and deterministic trace navigation
- Keywords: backlog-groom, request, bound hot endpoints and deterministic trace navigation, bounded slice
- Use when: Use when implementing or reviewing the delivery slice for Bound hot endpoints and deterministic trace navigation.
- Skip when: Skip when the change is unrelated to this delivery slice or its linked request.

# Priority
- Priority: High
- Rationale: La navigation doit etre bornee avant d'ajouter de nouveaux consommateurs UI.

# Notes
- Hybrid rationale: Derived from request `req_007_finaliser_workflow_diagnostic_et_clarifier_cantracediag` and kept bounded to one coherent delivery slice.
- Source file: `logics/request/req_007_finaliser_workflow_diagnostic_et_clarifier_cantracediag.md`.
- Generated locally by logics-manager.
- Task `task_018_bound_hot_endpoints_and_deterministic_trace_navigation` was finished via `logics-manager flow finish task` on 2026-07-18.

# Tasks
- `task_018_bound_hot_endpoints_and_deterministic_trace_navigation`
