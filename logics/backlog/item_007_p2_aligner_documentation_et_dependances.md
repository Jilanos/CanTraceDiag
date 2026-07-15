## item_007_p2_aligner_documentation_et_dependances - P2 Aligner documentation et dependances
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
La documentation, la roadmap, les ADR et les dépendances doivent refléter l'état livré
après durcissement, sans présenter des cibles comme déjà disponibles ni conserver des
dépendances inutiles ou non contraintes.

# Scope
- In:
  - alignement README, roadmap et ADR sur l'implémentation réellement livrée
  - distinction explicite entre cible produit, limites connues et état actuel
  - revue des dépendances inutilisées, non contraintes ou insuffisamment justifiées
  - documentation des budgets de performance retenus et de leur environnement
  - lint frontend ou alternative documentée pour maîtriser le JavaScript vanilla
- Out:
  - changement fonctionnel majeur
  - packaging Windows natif
  - réécriture complète du frontend

# Acceptance criteria
- AC16: README, roadmap et ADR distinguent clairement l'implémentation livrée de la cible,
  et les dépendances inutilisées ou non contraintes sont supprimées ou justifiées.

# AC Traceability
- request-AC16 -> This backlog slice. Proof: documentation matches delivered behavior and dependency hygiene is explicit.
- request-AC1 -> This backlog slice. Evidence needed: Tout arbitration ID défini par plusieurs DBC est détecté, y compris lorsque le nom
- request-AC2 -> This backlog slice. Evidence needed: Toute résolution DBC est exhaustive, validée contre les choix disponibles,
- request-AC3 -> This backlog slice. Evidence needed: L'ordre de sélection ou d'upload des DBC ne change jamais silencieusement les
- request-AC4 -> This backlog slice. Evidence needed: Les noms, unités, valeurs et détails provenant des ASC/DBC sont rendus comme texte,
- request-AC5 -> This backlog slice. Evidence needed: La CI installe les extras nécessaires depuis un environnement propre et exécute
- request-AC6 -> This backlog slice. Evidence needed: Le stockage d'une analyse volumineuse utilise un fichier DuckDB/cache temporaire
- request-AC7 -> This backlog slice. Evidence needed: Une trace réelle ou synthétique représentative de 150 Mo avec DBC fait l'objet
- request-AC8 -> This backlog slice. Evidence needed: L'import expose des phases et une progression mesurable, peut être annulé, retourne
- request-AC9 -> This backlog slice. Evidence needed: Une DBC invalide, une résolution incomplète/inconnue, deux basenames identiques et
- request-AC10 -> This backlog slice. Evidence needed: La vue trace filtre côté serveur par signal en combinaison avec temps, ID, message,
- request-AC11 -> This backlog slice. Evidence needed: La recherche de signaux couvre message, signal, ID, unité et DBC, et permet de
- request-AC12 -> This backlog slice. Evidence needed: Les colonnes pertinentes proposent les formats attendus (temps, hexadécimal,
- request-AC13 -> This backlog slice. Evidence needed: Aucun contrôle principal ne sort du viewport à 1280x720, 1024x768 et 390x844 ; à
- request-AC14 -> This backlog slice. Evidence needed: Le graphe et les commandes critiques ont des noms accessibles, un focus visible et
- request-AC15 -> This backlog slice. Evidence needed: Les états vide, chargement et erreur guident l'opérateur sans texte permanent de

# Delivery notes
- Traiter ce lot après les lots fonctionnels pour éviter de documenter une cible mouvante.
- Conserver les chemins dans les docs Logics en relatif au dépôt.

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
- Primary task(s): `task_007_p2_aligner_documentation_et_dependances`

# AI Context
- Summary: Align README, roadmap, ADRs and dependencies with the hardened implementation
  and documented performance budgets.
- Keywords: backlog-groom, request, p2 aligner documentation et dependances, bounded slice
- Use when: Use when implementing or reviewing the delivery slice for P2 Aligner documentation et dependances.
- Skip when: Skip when the change is unrelated to this delivery slice or its linked request.

# Priority
- Priority: Low
- Rationale: Important pour la maintenabilité, mais sans impact immédiat supérieur aux
  risques de justesse, sécurité, performance et utilisabilité.

# Notes
- Hybrid rationale: Derived from request `req_002_fiabiliser_cantracediag_apres_audit_fonctionnel_ui_et_performance` and kept bounded to one coherent delivery slice.
- Source file: `logics/request/req_002_fiabiliser_cantracediag_apres_audit_fonctionnel_ui_et_performance.md`.
- Generated locally by logics-manager.
- Task `task_007_p2_aligner_documentation_et_dependances` was finished via `logics-manager flow finish task` on 2026-07-15.

# Tasks
- `task_007_p2_aligner_documentation_et_dependances`
