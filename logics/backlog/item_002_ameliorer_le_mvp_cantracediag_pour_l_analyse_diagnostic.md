## item_002_ameliorer_le_mvp_cantracediag_pour_l_analyse_diagnostic - Améliorer le MVP CanTraceDiag pour l'analyse diagnostic
> From version: 1.0.0
> Schema version: 1.0
> Status: Ready
> Understanding: 90%
> Confidence: 85%
> Progress: 0%
> Complexity: High
> Theme: Operator workflow and runtime integration
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
Transformer le MVP technique actuel en un outil de diagnostic local utilisable au quotidien par un ingénieur CAN.
Prioriser les améliorations qui accélèrent l'analyse d'une trace réelle : navigation temporelle, comparaison de signaux, corrélation graphe/trace, recherche et filtrage.
Rendre l'interface plus professionnelle, dense et orientée atelier diagnostic, sans basculer dans une landing page ou une UI décorative.
Solidifier la tenue aux grosses traces observées localement, notamment les traces autour de 40 à 150 Mo et jusqu'à environ 1,2M frames utiles.
Rendre le comportement multi-DBC explicite, notamment quand plusieurs DBC revendiquent le même arbitration id.

# Scope
- In:
  - English four-zone diagnostic workspace.
  - Collapsible signal explorer and collapsible inspector.
  - A/B cursor workflow with nearest-sample values and deltas.
  - Graph/trace synchronization in both directions.
  - Trace filtering and selected-frame inspection.
  - DBC conflict popup during loading.
  - Server-side safeguards for large series queries and significant trace imports.
  - Local persistence for layout, selected signals, favorites, columns, and key filters.
- Out:
  - Real-time replay controls.
  - BLF/MF4 import.
  - Multi-bus advanced workflows.
  - Native Windows packaging.
  - Cloud or shared trace storage.
  - CSV export as priority work.
  - Mandatory acceptance against a 148 MB real trace.

# Delivery plan
- Wave 1: UI foundation
  - Convert user-facing UI text to English.
  - Build the four-zone workspace: top import/status bar, collapsible signal explorer, plot workspace, trace table, collapsible inspector.
  - Replace emoji buttons with icon-style controls and tooltips.
  - Persist panel collapsed state, panel sizes, selected signals, favorites, columns, and key filters in local storage.
- Wave 2: Interactive diagnosis
  - Add plot zoom, pan, fit/reset controls.
  - Add A/B cursors, nearest-sample readouts, and per-signal delta values.
  - Connect trace row selection to plot cursor positioning.
  - Connect plot click/selection to nearest trace rows.
- Wave 3: Trace search and inspection
  - Add filters for time window, arbitration id, decoded message, direction, decode status, and event type.
  - Populate the inspector with selected frame/event details and decoded signal values.
  - Add import/decode summary for unknown IDs, decode errors, and event counts.
- Wave 4: DBC conflicts and performance
  - Detect conflicts before finalizing a load.
  - Show a loading-time modal: "DBC conflict: which database should be used?".
  - Apply user-selected DBC per conflicting arbitration id and make the chosen DBC visible in trace/inspector.
  - Add server-side series downsampling/windowing and import progress/error reporting.

# Acceptance criteria
- AC1: L'utilisateur peut zoomer, paner et remettre à l'échelle les graphes temporels sans recharger toute la trace dans le navigateur.
- AC2: L'utilisateur peut poser deux curseurs A/B et lire les deltas temps et valeurs pour chaque signal sélectionné, sans interpolation.
- AC3: Un clic sur une frame de la trace positionne le curseur graphe au timestamp correspondant, et un clic dans le graphe permet d'atteindre les frames proches dans la vue trace.
- AC4: La vue trace propose des filtres combinables par fenêtre temporelle, ID, message, direction, decode status et type d'événement.
- AC5: L'explorateur de signaux permet de rechercher, grouper par DBC/message, sélectionner rapidement, marquer des favoris, et se replier facilement.
- AC6: L'UI expose un panneau inspecteur qui détaille la frame sélectionnée : timestamp, canal, ID, direction, DLC, data hex, message décodé, signaux physiques, statut decode et DBC utilisée si disponible.
- AC7: Les préférences utilisateur locales sont persistées : signaux sélectionnés, tailles des panneaux, colonnes trace, filtres principaux et favoris.
- AC8: L'import de traces réelles de taille significative reste utilisable localement sans pic mémoire disproportionné, avec une progression visible et une erreur claire en cas d'échec ; une trace réelle de 148 Mo peut servir de preuve manuelle si disponible, mais n'est pas obligatoire comme critère bloquant.
- AC9: Les séries graphées sont downsamplées ou fenêtrées côté serveur pour éviter d'envoyer massivement des points inutiles au navigateur.
- AC10: Au chargement, les conflits DBC sont détectés et une popup demande quelle DBC utiliser pour les arbitration ids en conflit avant de finaliser l'analyse.
- AC11: Le style UI est homogène, en anglais, dense, sans emojis dans les contrôles principaux, et vérifié sur desktop ainsi que sur une largeur réduite.
- AC12: Les validations couvrent les parcours critiques : import, filtres trace, curseurs A/B, synchro graphe/trace, downsampling, conflits DBC et persistance locale.

# AC Traceability
- request-AC1 -> This backlog slice. Proof: AC1: L'utilisateur peut zoomer, paner et remettre à l'échelle les graphes temporels sans recharger toute la trace dans le navigateur.
- request-AC2 -> This backlog slice. Proof: AC2: L'utilisateur peut poser deux curseurs A/B et lire les deltas temps et valeurs pour chaque signal sélectionné, sans interpolation.
- request-AC3 -> This backlog slice. Proof: AC3: Un clic sur une frame de la trace positionne le curseur graphe au timestamp correspondant, et un clic dans le graphe permet d'atteindre les frames proches dans la vue trace.
- request-AC4 -> This backlog slice. Proof: AC4: La vue trace propose des filtres combinables par fenêtre temporelle, ID, message, direction, decode status et type d'événement.
- request-AC5 -> This backlog slice. Proof: AC5: L'explorateur de signaux permet de rechercher, grouper par DBC/message, sélectionner rapidement, marquer des favoris, et se replier facilement.
- request-AC6 -> This backlog slice. Proof: AC6: L'UI expose un panneau inspecteur qui détaille la frame sélectionnée : timestamp, canal, ID, direction, DLC, data hex, message décodé, signaux physiques, statut decode et DBC utilisée si disponible.
- request-AC7 -> This backlog slice. Proof: AC7: Les préférences utilisateur locales sont persistées : signaux sélectionnés, tailles des panneaux, colonnes trace, filtres principaux et favoris.
- request-AC8 -> This backlog slice. Proof: AC8: L'import de traces réelles de taille significative reste utilisable localement sans pic mémoire disproportionné, avec une progression visible et une erreur claire en cas d'échec ; une trace réelle de 148 Mo peut servir de preuve manuelle si disponible, mais n'est pas obligatoire comme critère bloquant.
- request-AC9 -> This backlog slice. Proof: AC9: Les séries graphées sont downsamplées ou fenêtrées côté serveur pour éviter d'envoyer massivement des points inutiles au navigateur.
- request-AC10 -> This backlog slice. Proof: AC10: Au chargement, les conflits DBC sont détectés et une popup demande quelle DBC utiliser pour les arbitration ids en conflit avant de finaliser l'analyse.
- request-AC11 -> This backlog slice. Proof: AC11: Le style UI est homogène, en anglais, dense, sans emojis dans les contrôles principaux, et vérifié sur desktop ainsi que sur une largeur réduite.
- request-AC12 -> This backlog slice. Proof: AC12: Les validations couvrent les parcours critiques : import, filtres trace, curseurs A/B, synchro graphe/trace, downsampling, conflits DBC et persistance locale.

# Decision framing
- Product framing: Existing product brief is sufficient; this backlog refines the post-MVP diagnostic workflow.
- Product signals: English UI, four-zone workspace, A/B cursors first, DBC conflict popup at load time, exports not priority.
- Product follow-up: Update product docs only if the UI direction or priority order changes.
- Architecture framing: Existing architecture remains valid, but DBC conflict resolution and downsampling may require API/store changes.
- Architecture signals: local FastAPI/DuckDB architecture is retained; no packaging or cloud shift.
- Architecture follow-up: Create a new ADR only if a plotting library, frontend framework, persistent cache format, or non-DuckDB storage strategy is introduced.

# Links
- Product brief(s): `prod_002_product_brief_cantracediag_mvp`
- Architecture decision(s): `adr_002_adr_architecture_cantracediag_mvp`
- Request: `logics/request/req_001_ameliorer_mvp_cantracediag_analyse_diagnostic.md`
- Primary task(s): (none yet)

# AI Context
- Summary: Deliver the first post-MVP improvement slice for CanTraceDiag: English diagnostic workspace, collapsible explorer/inspector, A/B cursors, graph/trace sync, trace filters, DBC conflict popup, and large-series safeguards.
- Keywords: cantracediag, diagnostic-ui, english-ui, ab-cursors, trace-filters, graph-sync, dbc-conflict, downsampling, duckdb, fastapi
- Use when: Implementing, reviewing, or testing the improved diagnostic workflow after the initial MVP.
- Skip when: Work targets BLF/MF4, replay controls, packaging, cloud, or unrelated backend refactors.

# Priority
- Priority: High
- Rationale: This is the main path from a technically complete MVP to a usable diagnostic tool; A/B cursors and graph/trace synchronization unlock the highest immediate operator value.

# Notes
- Hybrid rationale: Derived from request `req_001_ameliorer_mvp_cantracediag_analyse_diagnostic` and kept bounded to one coherent delivery slice.
- Source file: `logics/request/req_001_ameliorer_mvp_cantracediag_analyse_diagnostic.md`.
- Generated locally by logics-manager.

# Tasks
- `task_002_ameliorer_le_mvp_cantracediag_pour_l_analyse_diagnostic`
