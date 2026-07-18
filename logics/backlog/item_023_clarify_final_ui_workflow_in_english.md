## item_023_clarify_final_ui_workflow_in_english - Clarify final UI workflow in English
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
Toutes les fonctions sont exposees sur un seul plan dense, les erreurs remplacent le
resume global et les filtres actifs manquent de hierarchie. La refonte finale doit
s'appuyer sur les contrats et modules stabilises par les six slices precedentes.

# Scope
- In:
  - onglets centraux Analysis/Trace/Report avec contexte lateral persistant
  - interface et documentation utilisateur exclusivement en anglais
  - erreurs contextualisees, relance, etats vides et criteres actifs supprimables
  - presets persistants Plots/Trace/Full diagnostic
- Out:
  - theme clair et changement de l'identite instrument de mesure
  - nouveau framework frontend ou nouvelle fonction metier

# Acceptance criteria
- AC4: L'interface propose les onglets `Analysis`, `Trace` et `Report` sans perdre
- AC5: Tous les libelles, actions, messages, etats vides et contenus de documentation
- AC6: Une erreur de serie, table, inspecteur ou export est affichee dans le composant
- AC7: La trace affiche un etat vide distinct pour « aucune trace », « aucun resultat

# AC Traceability
- request-AC4 -> This backlog slice. Proof: AC4: L'interface propose les onglets `Analysis`, `Trace` et `Report` sans perdre
- request-AC5 -> This backlog slice. Proof: AC5: Tous les libelles, actions, messages, etats vides et contenus de documentation
- request-AC6 -> This backlog slice. Proof: AC6: Une erreur de serie, table, inspecteur ou export est affichee dans le composant
- request-AC7 -> This backlog slice. Proof: AC7: La trace affiche un etat vide distinct pour « aucune trace », « aucun resultat

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
- Summary: Clarify final UI workflow in English
- Keywords: backlog-groom, request, clarify final ui workflow in english, bounded slice
- Use when: Use when implementing or reviewing the delivery slice for Clarify final UI workflow in English.
- Skip when: Skip when the change is unrelated to this delivery slice or its linked request.

# Priority
- Priority: Medium
- Rationale: Forte valeur utilisateur, volontairement livree en dernier apres stabilisation.

# Notes
- Hybrid rationale: Derived from request `req_007_finaliser_workflow_diagnostic_et_clarifier_cantracediag` and kept bounded to one coherent delivery slice.
- Source file: `logics/request/req_007_finaliser_workflow_diagnostic_et_clarifier_cantracediag.md`.
- Generated locally by logics-manager.

# Tasks
- `task_023_clarify_final_ui_workflow_in_english`
