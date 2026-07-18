## item_021_improve_accessibility_and_minimal_responsive_support - Improve accessibility and minimal responsive support
> From version: 0.1.0
> Schema version: 1.0
> Status: Ready
> Understanding: 90%
> Confidence: 85%
> Progress: 0%
> Complexity: High
> Theme: Operator workflow and runtime integration
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
Plusieurs controles restent souris seulement et les formats desktop intermediaires ne
sont pas proteges par des tests de debordement. Le mobile doit garder les actions
critiques accessibles sans devenir une cible d'analyse complete.

# Scope
- In:
  - clavier et noms accessibles pour controles, lignes, dialogues et resizers
  - Pointer Events pour graphe et redimensionnement
  - viewports E2E 1024x768, 1280x720, 1600x900 et support critique 390x844
  - E2E navigateur obligatoires en CI
- Out:
  - experience d'analyse complete sur mobile
  - theme clair

# Acceptance criteria
- AC13: Les favoris, filtres, onglets, lignes de table, dialogues et redimensionneurs
- AC14: Aucun controle principal ne deborde a 1024x768, 1280x720 et 1600x900. A

# AC Traceability
- request-AC13 -> This backlog slice. Proof: AC13: Les favoris, filtres, onglets, lignes de table, dialogues et redimensionneurs
- request-AC14 -> This backlog slice. Proof: AC14: Aucun controle principal ne deborde a 1024x768, 1280x720 et 1600x900. A

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
- Summary: Improve accessibility and minimal responsive support
- Keywords: backlog-groom, request, improve accessibility and minimal responsive support, bounded slice
- Use when: Use when implementing or reviewing the delivery slice for Improve accessibility and minimal responsive support.
- Skip when: Skip when the change is unrelated to this delivery slice or its linked request.

# Priority
- Priority: Medium
- Rationale: Important pour l'usage, mais depend des contrats stabilises par les slices P0/P1.

# Notes
- Hybrid rationale: Derived from request `req_007_finaliser_workflow_diagnostic_et_clarifier_cantracediag` and kept bounded to one coherent delivery slice.
- Source file: `logics/request/req_007_finaliser_workflow_diagnostic_et_clarifier_cantracediag.md`.
- Generated locally by logics-manager.

# Tasks
- `task_021_improve_accessibility_and_minimal_responsive_support`
