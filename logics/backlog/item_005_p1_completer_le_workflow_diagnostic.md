## item_005_p1_completer_le_workflow_diagnostic - P1 Completer le workflow diagnostic
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
Le workflow diagnostic annonce des filtres, recherches et formats utiles à l'analyse CAN,
mais certains chemins ne sont pas encore complets côté API, trace paginée et persistance
des préférences.

# Scope
- In:
  - filtre serveur par signal combinable avec les filtres existants
  - recherche signal par message, signal, ID, unité et DBC
  - distinction claire entre signaux présents dans la trace et signaux issus de la DBC
    retenue
  - formats de colonnes temps, ID, DLC et data selon les besoins diagnostic
  - largeur de colonnes maîtrisée et préférences persistées
  - rapport d'import exposant les décisions DBC et anomalies utiles
- Out:
  - nouveaux formats de trace hors ASC
  - refonte complète de l'interface en framework
  - fonctions avancées multi-bus

# Acceptance criteria
- AC10: La vue trace filtre côté serveur par signal en combinaison avec temps, ID, message,
  direction, statut et événement.
- AC11: La recherche de signaux couvre message, signal, ID, unité et DBC, et permet de
  distinguer les signaux présents dans la trace et ceux issus de la DBC retenue.
- AC12: Les colonnes pertinentes proposent les formats attendus (temps, hexadécimal,
  décimal, binaire), une largeur réellement maîtrisée et une persistance testée.

# AC Traceability
- request-AC10 -> This backlog slice. Proof: server-side signal filtering with existing filters.
- request-AC11 -> This backlog slice. Proof: broadened signal search and present/DBC distinction.
- request-AC12 -> This backlog slice. Proof: tested column formats, widths and persistence.
- request-AC1 -> This backlog slice. Evidence needed: Tout arbitration ID défini par plusieurs DBC est détecté, y compris lorsque le nom
- request-AC2 -> This backlog slice. Evidence needed: Toute résolution DBC est exhaustive, validée contre les choix disponibles,
- request-AC3 -> This backlog slice. Evidence needed: L'ordre de sélection ou d'upload des DBC ne change jamais silencieusement les
- request-AC4 -> This backlog slice. Evidence needed: Les noms, unités, valeurs et détails provenant des ASC/DBC sont rendus comme texte,
- request-AC5 -> This backlog slice. Evidence needed: La CI installe les extras nécessaires depuis un environnement propre et exécute
- request-AC6 -> This backlog slice. Evidence needed: Le stockage d'une analyse volumineuse utilise un fichier DuckDB/cache temporaire
- request-AC7 -> This backlog slice. Evidence needed: Une trace réelle ou synthétique représentative de 150 Mo avec DBC fait l'objet
- request-AC8 -> This backlog slice. Evidence needed: L'import expose des phases et une progression mesurable, peut être annulé, retourne
- request-AC9 -> This backlog slice. Evidence needed: Une DBC invalide, une résolution incomplète/inconnue, deux basenames identiques et
- request-AC13 -> This backlog slice. Evidence needed: Aucun contrôle principal ne sort du viewport à 1280x720, 1024x768 et 390x844 ; à
- request-AC14 -> This backlog slice. Evidence needed: Le graphe et les commandes critiques ont des noms accessibles, un focus visible et
- request-AC15 -> This backlog slice. Evidence needed: Les états vide, chargement et erreur guident l'opérateur sans texte permanent de
- request-AC16 -> This backlog slice. Evidence needed: README, roadmap et ADR distinguent clairement l'implémentation livrée de la cible,

# Delivery notes
- Prioriser les API et tests avant le polissage visuel pour éviter un filtre seulement
  cosmétique.
- Les choix DBC issus du P0 doivent être consommés comme source de vérité.

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
- Request: `req_002_fiabiliser_cantracediag_apres_audit_fonctionnel_ui_et_performance`
- Primary task(s): `task_005_p1_completer_le_workflow_diagnostic`

# AI Context
- Summary: Complete diagnostic filtering, signal search, column formats and import report
  behavior after DBC decisions are reliable.
- Keywords: backlog-groom, request, p1 completer le workflow diagnostic, bounded slice
- Use when: Use when implementing or reviewing the delivery slice for P1 Completer le workflow diagnostic.
- Skip when: Skip when the change is unrelated to this delivery slice or its linked request.

# Priority
- Priority: Medium
- Rationale: Ces fonctions ferment les écarts du backlog P0 mais dépendent d'abord de la
  fiabilité DBC et de l'import robuste.

# Notes
- Hybrid rationale: Derived from request `req_002_fiabiliser_cantracediag_apres_audit_fonctionnel_ui_et_performance` and kept bounded to one coherent delivery slice.
- Source file: `logics/request/req_002_fiabiliser_cantracediag_apres_audit_fonctionnel_ui_et_performance.md`.
- Generated locally by logics-manager.
- Task `task_005_p1_completer_le_workflow_diagnostic` was finished via `logics-manager flow finish task` on 2026-07-15.

# Tasks
- `task_005_p1_completer_le_workflow_diagnostic`
