## item_009_p1_optimiser_endpoints_chauds - P1 Optimiser endpoints chauds
> From version: 1.0.0
> Schema version: 1.0
> Status: Obsolete
> Understanding: 100%
> Confidence: 100%
> Progress: 0%
> Complexity: High
> Theme: Operator workflow and runtime integration
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
Rendre l'import réellement asynchrone : il ne doit plus geler l'API, doit exposer une
Éliminer les courses d'état de session : aucun remplacement de store ne doit casser
Rendre les erreurs visibles et actionnables dans l'UI : plus aucun échec réseau
Ramener les endpoints chauds (curseur, pagination trace, séries) à un coût borné,
Livrer l'export des données (CSV et Parquet) sur la sélection de signaux et la plage
Restreindre la surface réseau locale : l'API ne doit pas être exploitable par DNS
Corriger le responsive 1280x720 / 1024x768, l'accessibilité des favoris, filtres et
Réduire la dette : parsing ASC robuste aux lignes tronquées et timestamps négatifs,

# Scope
- In:
  - one coherent delivery slice from the source request
- Out:
  - unrelated sibling slices that should stay in separate backlog items instead of widening this doc

# Acceptance criteria
- AC5: `/api/cursor` n'exécute plus de scan complet (plan de requête borné ou mesure
- AC6: La pagination de la trace est stable et déterministe : tri `(timestamp_s,

# AC Traceability
- request-AC5 -> This backlog slice. Proof: AC5: `/api/cursor` n'exécute plus de scan complet (plan de requête borné ou mesure
- request-AC6 -> This backlog slice. Proof: AC6: La pagination de la trace est stable et déterministe : tri `(timestamp_s,

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
- Request: `logics/request/req_003_robustesse_execution_et_completude_post_audit_2026_07_16.md`
- Primary task(s): (none yet)
- Superseded by: `item_018_bound_hot_endpoints_and_deterministic_trace_navigation`

# AI Context
- Summary: P1 Optimiser endpoints chauds
- Keywords: backlog-groom, request, p1 optimiser endpoints chauds, bounded slice
- Use when: Use when implementing or reviewing the delivery slice for P1 Optimiser endpoints chauds.
- Skip when: Skip when the change is unrelated to this delivery slice or its linked request.

# Priority
- Priority: Medium
- Rationale: Default until groomed.

# Notes
- Hybrid rationale: Derived from request `req_003_robustesse_execution_et_completude_post_audit_2026_07_16` and kept bounded to one coherent delivery slice.
- Source file: `logics/request/req_003_robustesse_execution_et_completude_post_audit_2026_07_16.md`.
- Generated locally by logics-manager.

# Tasks
- `task_009_p1_optimiser_endpoints_chauds`
