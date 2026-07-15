## item_006_p1_rendre_interface_responsive_et_accessible - P1 Rendre interface responsive et accessible
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
À 1280 px et en mode étroit, des commandes principales sortent du viewport ou deviennent
difficiles à atteindre. Les interactions critiques doivent rester disponibles au clavier
et porter des noms accessibles sans transformer l'atelier en application mobile complète.

# Scope
- In:
  - comportement responsive explicite pour 1280x720, 1024x768 et 390x844
  - garantie qu'aucune action critique n'est inaccessible ou masquée silencieusement en
    mode étroit
  - focus visible et noms accessibles pour graphe et commandes critiques
  - alternatives clavier pour curseurs, favoris, panneaux et ordre des colonnes
  - états vide, chargement et erreur orientés opérateur
- Out:
  - expérience mobile complète
  - refonte esthétique globale
  - ajout de texte permanent de mode d'emploi dans les barres d'outils

# Acceptance criteria
- AC13: Aucun contrôle principal ne sort du viewport à 1280x720, 1024x768 et 390x844 ; à
  390x844, aucune action critique n'est inaccessible ou masquée silencieusement, même si
  l'expérience reste prioritairement desktop.
- AC14: Le graphe et les commandes critiques ont des noms accessibles, un focus visible et
  une alternative clavier pour curseurs, favoris, panneaux et ordre des colonnes.
- AC15: Les états vide, chargement et erreur guident l'opérateur sans texte permanent de
  mode d'emploi dans les barres d'outils.

# AC Traceability
- request-AC13 -> This backlog slice. Proof: viewport checks at 1280x720, 1024x768 and 390x844.
- request-AC14 -> This backlog slice. Proof: accessible names, focus and keyboard alternatives.
- request-AC15 -> This backlog slice. Proof: useful empty/loading/error states without toolbar tutorials.
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
- request-AC16 -> This backlog slice. Evidence needed: README, roadmap et ADR distinguent clairement l'implémentation livrée de la cible,

# Delivery notes
- Le critère mobile est une contrainte d'accès aux actions critiques, pas une promesse de
  confort complet sur téléphone.
- Valider par captures Playwright ou assertions de viewport sur les largeurs cibles.

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
- Primary task(s): `task_006_p1_rendre_interface_responsive_et_accessible`

# AI Context
- Summary: Keep critical controls reachable at target widths and add keyboard/accessibility
  coverage without a full mobile redesign.
- Keywords: backlog-groom, request, p1 rendre interface responsive et accessible, bounded slice
- Use when: Use when implementing or reviewing the delivery slice for P1 Rendre interface responsive et accessible.
- Skip when: Skip when the change is unrelated to this delivery slice or its linked request.

# Priority
- Priority: Medium
- Rationale: Le défaut bloque les écrans étroits, tandis que le cas d'usage principal
  reste le poste desktop d'ingénierie.

# Notes
- Hybrid rationale: Derived from request `req_002_fiabiliser_cantracediag_apres_audit_fonctionnel_ui_et_performance` and kept bounded to one coherent delivery slice.
- Source file: `logics/request/req_002_fiabiliser_cantracediag_apres_audit_fonctionnel_ui_et_performance.md`.
- Generated locally by logics-manager.
- Task `task_006_p1_rendre_interface_responsive_et_accessible` was finished via `logics-manager flow finish task` on 2026-07-15.

# Tasks
- `task_006_p1_rendre_interface_responsive_et_accessible`
