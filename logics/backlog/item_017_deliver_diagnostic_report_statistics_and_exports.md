## item_017_deliver_diagnostic_report_statistics_and_exports - Deliver diagnostic report statistics and exports
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
CanTraceDiag permet d'analyser une trace mais ne ferme pas le workflow : aucune
synthese d'import dediee, statistique de plage ou sortie CSV/Parquet n'est disponible.
L'operateur doit pouvoir qualifier puis extraire son diagnostic sans outil intermediaire.

# Scope
- In:
  - synthese d'import avec fichier, plage, duree, DBC utilisees, volumes et anomalies
  - statistiques numeriques et repartition des valeurs textuelles entre A et B
  - export long CSV/Parquet et CSV large optionnel pour trois portees explicites
  - generation en flux et tests de memoire bornee
- Out:
  - hierarchie finale Analysis/Trace/Report, traitee par `item_023`
  - comparaison de traces, signaux calcules et annotations

# Acceptance criteria
- AC1: Une vue `Report` fournit une synthese de l'import avec le fichier analyse, la
- AC2: L'utilisateur exporte en CSV et Parquet les signaux selectionnes sur la plage
- AC3: La vue `Analysis` affiche par signal numerique selectionne le nombre

# AC Traceability
- request-AC1 -> This backlog slice. Proof: AC1: Une vue `Report` fournit une synthese de l'import avec le fichier analyse, la
- request-AC2 -> This backlog slice. Proof: AC2: L'utilisateur exporte en CSV et Parquet les signaux selectionnes sur la plage
- request-AC3 -> This backlog slice. Proof: AC3: La vue `Analysis` affiche par signal numerique selectionne le nombre

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
- Summary: Deliver diagnostic report statistics and exports
- Keywords: backlog-groom, request, deliver diagnostic report statistics and exports, bounded slice
- Use when: Use when implementing or reviewing the delivery slice for Deliver diagnostic report statistics and exports.
- Skip when: Skip when the change is unrelated to this delivery slice or its linked request.

# Priority
- Priority: High
- Rationale: C'est la premiere slice et la principale fermeture du workflow diagnostic.

# Notes
- Hybrid rationale: Derived from request `req_007_finaliser_workflow_diagnostic_et_clarifier_cantracediag` and kept bounded to one coherent delivery slice.
- Source file: `logics/request/req_007_finaliser_workflow_diagnostic_et_clarifier_cantracediag.md`.
- Generated locally by logics-manager.

# Tasks
- `task_017_deliver_diagnostic_report_statistics_and_exports`
