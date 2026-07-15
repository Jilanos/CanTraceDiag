## req_001_ameliorer_mvp_cantracediag_analyse_diagnostic - Améliorer le MVP CanTraceDiag pour l'analyse diagnostic
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: Transformer le MVP technique actuel en outil de diagnostic local utilisable au quotidien, en priorisant ergonomie UI, curseurs synchronisés, filtres trace, performance grosses traces et résolution des ambiguïtés DBC.
> Confidence: high
> Complexity: high
> Theme: product-ux
> Reminder: Update status/understanding/confidence and linked backlog/task references when you edit this doc.

# Needs
- Transformer le MVP technique actuel en un outil de diagnostic local utilisable au quotidien par un ingénieur CAN.
- Prioriser les améliorations qui accélèrent l'analyse d'une trace réelle : navigation temporelle, comparaison de signaux, corrélation graphe/trace, recherche et filtrage.
- Rendre l'interface plus professionnelle, dense et orientée atelier diagnostic, sans basculer dans une landing page ou une UI décorative.
- Solidifier la tenue aux grosses traces observées localement, notamment les traces autour de 40 à 150 Mo et jusqu'à environ 1,2M frames utiles.
- Rendre le comportement multi-DBC explicite, notamment quand plusieurs DBC revendiquent le même arbitration id.

# Context
- `req_000_mvp_analyse_locale_traces_can_asc` est livré et marqué `Done`.
- Le MVP actuel fournit une chaîne bout en bout : import `.asc`, chargement DBC, décodage `cantools`, index DuckDB, API FastAPI, UI locale avec signaux, graphes empilés et vue trace.
- Les validations actuelles passent : `pytest` 30 tests, `ruff`, `logics-manager lint --require-status`, `logics-manager health`.
- Les principales limites produit constatées sont :
  - import encore eager en mémoire avant insertion DuckDB ;
  - séries graphe chargées en masse côté navigateur sans downsampling piloté par la largeur écran ;
  - un seul curseur simple, sans delta A/B ;
  - synchronisation graphe -> trace et trace -> graphe absente ;
  - vue trace paginée mais pas encore confortable pour la recherche diagnostic ;
  - conflits DBC seulement signalés, sans choix utilisateur de priorité ou de résolution ;
  - UI actuelle fonctionnelle mais brute, mixte anglais/français, avec des boutons textuels/emoji et peu de hiérarchie métier.

# Product direction
- Le premier écran doit rester l'outil lui-même : pas de page marketing.
- Tout le texte visible dans l'UI cible doit être en anglais.
- L'interface cible est un atelier diagnostic dense :
  - barre haute compacte pour import, statut, résumé acquisition et actions principales ;
  - sidebar gauche repliable pour explorer les DBC, messages et signaux ;
  - zone centrale pour les graphes temporels synchronisés ;
  - zone basse pour la trace CAN filtrable ;
  - panneau droit inspecteur repliable pour la frame ou le signal sélectionné.
- Les actions fréquentes doivent être accessibles par icônes avec tooltips : zoom, fit, curseur A, curseur B, reset, export, lock axes, colonnes.
- Les textes utilisateur doivent être cohérents en anglais dans un premier temps.
- Le style doit rester sobre et technique : fond sombre neutre, panneaux contrastés, accent cyan/vert, warning ambre, erreur rouge, palette signaux lisible et non dominée par un seul bleu.

# Priorities
- P0: Améliorer l'analyse interactive.
  - Ajouter zoom/pan temporel sur les graphes.
  - Ajouter deux curseurs A/B avec delta temps et delta valeur par signal.
  - Synchroniser clic graphe vers ligne trace la plus proche.
  - Synchroniser clic trace vers curseur graphe.
  - Ajouter filtres trace rapides : id, message, direction, statut decode, événements, fenêtre temporelle.
- P1: Rendre l'UI prête pour usage quotidien.
  - Remplacer les emojis par des contrôles iconographiques sobres avec tooltips.
  - Ajouter un layout quatre zones : signal explorer, plots, trace, inspector.
  - Permettre le repli facile du signal explorer et de l'inspector.
  - Ajouter favoris/pins de signaux et groupes par message/DBC.
  - Sauvegarder layout utilisateur : signaux sélectionnés, tailles panneaux, colonnes, filtres.
- P1: Solidifier les grosses traces.
  - Importer par chunks au lieu de charger toute la trace en listes Python.
  - Insérer frames/events/samples dans DuckDB par lots.
  - Ajouter indexes ou stratégies de requête pour `timestamp_s`, `arbitration_id`, `(message_name, signal_name, timestamp_s)`.
  - Ajouter downsampling serveur pour adapter chaque série à la largeur visible.
  - Afficher progression import et état d'erreur exploitable.
- P2: Améliorer la gestion DBC.
  - Lors du chargement, afficher une popup si des conflits DBC sont détectés.
  - La popup doit demander quelle DBC utiliser pour les IDs en conflit, avec une formulation du type : "DBC conflict: which database should be used?".
  - Permettre une résolution par arbitration id dans la popup de chargement.
  - Afficher la DBC utilisée pour chaque message décodé.
  - Produire un rapport d'import : IDs inconnus, decode errors, DBC inutilisées, messages jamais vus.
- P2: Ajouter les exports utiles.
  - Export CSV des signaux sélectionnés sur une fenêtre temporelle.
  - Export CSV de la trace filtrée.
  - Ces exports ne sont pas prioritaires et ne bloquent pas l'acceptation de cette request.

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

# Out of scope
- Replay temps réel lecture/pause/vitesse.
- Support BLF/MF4 complet.
- Multi-bus avancé.
- Collaboration multi-utilisateur.
- Packaging Windows natif.
- Cloud, base distante ou stockage partagé de traces.
- Refonte backend complète hors besoins de performance ci-dessus.

# Suggested implementation slices
- Slice 1: UI diagnostic foundation
  - Layout quatre zones : explorer/plots/trace/inspector.
  - Repli facile de l'explorer et de l'inspector.
  - Interface user-facing entièrement en anglais.
  - Remplacement des emojis par icônes/tooltips.
  - Persistance layout de base.
- Slice 2: Cursor and synchronization workflow
  - Zoom/pan/fit.
  - Curseurs A/B et deltas.
  - Clic trace -> graphe.
  - Clic graphe -> trace proche.
- Slice 3: Trace search and inspection
  - Filtres combinables.
  - Inspecteur frame/signaux.
  - Rapport decode status/unknown IDs.
- Slice 4: Large trace performance
  - Ingestion chunked.
  - Inserts DuckDB par lots.
  - Index/requêtes optimisées.
  - Downsampling serveur.
  - Progression import.
- Slice 5: DBC conflict workflow
  - Popup au chargement en cas de conflit DBC.
  - Choix de la DBC à utiliser par arbitration id conflictuel.
  - DBC source visible dans trace et inspecteur.

# Decisions
- D1: The improved MVP UI must be fully in English.
- D2: The target layout is a four-zone desktop diagnostic workspace: collapsible signal explorer on the left, plots in the upper center, trace table in the lower center, and collapsible inspector on the right.
- D3: A/B cursors are the first functional priority, before broader large-trace performance work, while keeping server-side downsampling close behind.
- D4: DBC conflicts must be handled during loading with a popup asking which DBC should be used for conflicting IDs.
- D5: A real 148 MB trace is useful for manual proof but is not mandatory as a blocking acceptance criterion.
- D6: CSV exports are not priority work for this request.

# Definition of Ready (DoR)
- [x] Problem statement is explicit and user impact is clear.
- [x] Scope boundaries (in/out) are explicit.
- [x] Acceptance criteria are testable.
- [x] Dependencies and known risks are listed.

# Dependencies and risks
- DuckDB remains the local query/index layer.
- FastAPI remains the local API host.
- The browser UI is currently vanilla JS/canvas; adding complex interactions may justify a small plotting/interaction library if vanilla implementation becomes brittle.
- Large trace validation depends on local real traces that must remain outside Git.
- Downsampling must preserve diagnostic meaning: min/max per bucket is preferred over average-only sampling for transient detection.
- DBC conflict resolution can change decoded values, so the selected priority must be visible and reproducible.

# Companion docs
- Product brief(s): `prod_002_product_brief_cantracediag_mvp`
- Architecture decision(s): `adr_002_adr_architecture_cantracediag_mvp`

# References
- `req_000_mvp_analyse_locale_traces_can_asc`
- `item_001_mvp_analyse_locale_traces_can_asc`
- `task_001_mvp_analyse_locale_traces_can_asc`
- `docs/product-brief.md`
- `docs/roadmap.md`
- `src/cantracediag/api.py`
- `src/cantracediag/pipeline.py`
- `src/cantracediag/store.py`
- `src/cantracediag/web/index.html`
- `src/cantracediag/web/app.js`

# AI Context
- Summary: Improve the delivered CanTraceDiag MVP into a daily diagnostic tool by focusing on UI workflows, A/B cursors, graph/trace synchronization, trace filtering, large trace performance, and DBC conflict resolution.
- Keywords: cantracediag, diagnostic-ui, can, asc, dbc, duckdb, fastapi, trace-view, cursors, downsampling, dbc-conflicts
- Use when: Planning backlog slices after the initial MVP, especially UI/UX, performance, trace navigation, and DBC ambiguity work.
- Skip when: Work targets first MVP delivery already covered by `req_000`, BLF/MF4 support, packaging, cloud usage, or real-time replay.

# Backlog
- `item_002_ameliorer_le_mvp_cantracediag_pour_l_analyse_diagnostic`
