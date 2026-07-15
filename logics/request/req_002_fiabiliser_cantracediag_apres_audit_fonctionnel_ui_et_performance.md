## req_002_fiabiliser_cantracediag_apres_audit_fonctionnel_ui_et_performance - Fiabiliser CanTraceDiag post-audit fonctionnel UI et performance
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: Corriger en priorité, dans un seul bloc P0, les risques de justesse DBC, de sécurité UI et de CI, puis traiter la scalabilité mémoire, le workflow diagnostic, le responsive minimal et les écarts de maintenabilité identifiés par l’audit bout en bout du 15 juillet 2026.
> Confidence: high
> Complexity: high
> Theme: quality-hardening
> Reminder: Update status/understanding/confidence and linked backlog/task references when you edit this doc.

# Needs
- Rendre le décodage multi-DBC déterministe, explicite et suffisamment fiable pour un
  diagnostic technique.
- Permettre l'import en arrière-plan de ce qui n'est pas ambigu, tout en demandant une
  confirmation explicite en pop-up pour les choix DBC ambigus.
- Supprimer les chemins d'injection HTML provenant des fichiers ASC/DBC importés.
- Tenir les traces cibles de 40 à 150 Mo avec un budget de temps et de mémoire documenté,
  une amélioration maximale raisonnable, une progression d'import réelle et des erreurs
  actionnables.
- Finaliser les filtres, formats et recherches annoncés dans le backlog P0.
- Rendre l'atelier diagnostic utilisable aux largeurs supportées et accessible au clavier
  sur les interactions critiques.
- Rétablir une CI reproductible et couvrir les risques identifiés par l'audit.

# Context
- L'audit complet est documenté dans `docs/audit-bout-en-bout-2026-07-15.md`.
- Le MVP actuel couvre déjà import ASC, DBC multiples, décodage, index DuckDB, API
  FastAPI, graphes empilés, zoom/pan, curseurs A/B, synchronisation graphe/trace, vue
  trace paginée, filtres principaux, inspecteur et préférences locales.
- Les validations locales passent : 50 tests Python/E2E et `ruff`.
- Les deux traces réelles hors dépôt contiennent environ 400k et 1,24M frames.
- L'import sans DBC prend 8,2 s / 396 Mo pour 44 Mo et 24,5 s / 630 Mo pour 155 Mo.
- La trace de 44 Mo avec 14 DBC produit 2,58M samples en 24,4 s avec un pic de 850 Mo.
- Les 14 DBC réelles contiennent deux conflits de noms différents et sept IDs dupliqués
  entre versions avec le même nom de message. Ces sept doublons ne sont pas signalés ;
  `0x723` contient trois ou quatre signaux selon la version.
- À 1280 px, le contenu mesure environ 1447 px et masque des commandes. À 390 px, la zone
  centrale est hors écran.
- Les champs de trace et DBC sont rendus via plusieurs affectations `innerHTML` sans
  échappement systématique.
- Le workflow CI installe `.[dev]` alors que les tests exigent aussi l'extra `api`.

# Product decisions
- Le premier lot doit livrer ensemble la justesse DBC, le rendu DOM sûr et la CI
  reproductible, afin de rétablir la confiance diagnostic avant les autres lots.
- Les conflits DBC ne bloquent pas l'import des frames non ambiguës : l'import continue en
  arrière-plan et les décisions ambiguës sont confirmées par l'opérateur dans une pop-up.
- Les tests de régression DBC utilisent des fixtures synthétiques reproduisant les motifs
  réels, sans intégrer les DBC ou traces réelles hors dépôt.
- La performance est traitée comme une optimisation mesurée au maximum raisonnable de ce
  qui est possible dans l'architecture locale, avec budget documenté plutôt qu'un seuil
  absolu imposé à l'avance.
- L'import asynchrone peut utiliser un état serveur temporaire adapté à l'atelier local ;
  une persistance durable des jobs après redémarrage navigateur n'est pas requise.
- Le mode `390x844` doit garantir qu'aucune action critique n'est inaccessible ou masquée
  silencieusement ; il n'a pas à devenir une expérience mobile complète.
- La CSP doit réduire le risque et accompagner le rendu texte sûr, sans imposer
  immédiatement une politique excluant `unsafe-inline` si cela dépasse le lot P0.

# Priorities
- P0 - Confiance diagnostic et sécurité, livré en un seul bloc : conflits DBC exhaustifs,
  résolution validée, import des frames non ambiguës, pop-up de choix ambigus, rendu DOM
  sûr, CSP pragmatique et CI reproductible.
- P1 - Scalabilité et robustesse : DuckDB disque/cache, budget mémoire, job d'import avec
  progression/annulation, erreurs métier, conservation transactionnelle de la session et
  amélioration mesurée au maximum raisonnable.
- P1 - Complétude produit : filtre signal, recherche ID/unité/DBC, formats ID/DLC/data,
  signal présent/absent et rapport d'import.
- P1 - UI et accessibilité : responsive desktop compact/mode étroit, clavier, noms
  accessibles, états vides et erreurs.
- P2 - Maintenabilité : documentation synchronisée, dépendances maîtrisées, découpage JS,
  lint frontend et budgets de performance.

# Acceptance criteria
- AC1: Tout arbitration ID défini par plusieurs DBC est détecté, y compris lorsque le nom
  de message est identique ; un doublon n'est auto-accepté que si une empreinte canonique
  démontre l'équivalence des définitions.
- AC2: Toute résolution DBC est exhaustive, validée contre les choix disponibles,
  confirmée par l'opérateur en pop-up lorsqu'elle est ambiguë, persistée avec l'analyse et
  visible dans le rapport d'import et l'inspecteur.
- AC3: L'ordre de sélection ou d'upload des DBC ne change jamais silencieusement les
  valeurs décodées ; des fixtures synthétiques reproduisent les motifs réels `0x710` et
  `0x720` à `0x725` sans dépendre des DBC réelles hors dépôt.
- AC4: Les noms, unités, valeurs et détails provenant des ASC/DBC sont rendus comme texte,
  une CSP pragmatique est active et un test hostile prouve l'absence d'exécution HTML/JS.
- AC5: La CI installe les extras nécessaires depuis un environnement propre et exécute
  lint, tests API et tests E2E critiques sur une version Python supportée.
- AC6: Le stockage d'une analyse volumineuse utilise un fichier DuckDB/cache temporaire
  hors dépôt et ne dépend plus d'une base complète en mémoire.
- AC7: Une trace réelle ou synthétique représentative de 150 Mo avec DBC fait l'objet
  d'une optimisation au maximum raisonnable et d'un budget documenté de temps/mémoire ; la
  CI protège au moins un budget synthétique réduit et reproductible.
- AC8: L'import expose des phases et une progression mesurable, peut être annulé, retourne
  des erreurs actionnables, continue en arrière-plan pour les frames non ambiguës et ne
  détruit la session précédente qu'après succès validé.
- AC9: Une DBC invalide, une résolution incomplète/inconnue, deux basenames identiques et
  un payload tronqué ont des comportements déterministes, visibles et testés.
- AC10: La vue trace filtre côté serveur par signal en combinaison avec temps, ID, message,
  direction, statut et événement.
- AC11: La recherche de signaux couvre message, signal, ID, unité et DBC, et permet de
  distinguer les signaux présents dans la trace et ceux issus de la DBC retenue.
- AC12: Les colonnes pertinentes proposent les formats attendus (temps, hexadécimal,
  décimal, binaire), une largeur réellement maîtrisée et une persistance testée.
- AC13: Aucun contrôle principal ne sort du viewport à 1280x720, 1024x768 et 390x844 ; à
  390x844, aucune action critique n'est inaccessible ou masquée silencieusement, même si
  l'expérience reste prioritairement desktop.
- AC14: Le graphe et les commandes critiques ont des noms accessibles, un focus visible et
  une alternative clavier pour curseurs, favoris, panneaux et ordre des colonnes.
- AC15: Les états vide, chargement et erreur guident l'opérateur sans texte permanent de
  mode d'emploi dans les barres d'outils.
- AC16: README, roadmap et ADR distinguent clairement l'implémentation livrée de la cible,
  et les dépendances inutilisées ou non contraintes sont supprimées ou justifiées.

# Suggested implementation slices
- Slice 1: DBC correctness, safe rendering and CI repair.
- Slice 2: Disk-backed import pipeline, progress jobs and failure semantics.
- Slice 3: Trace filters, signal search, column formats and import report.
- Slice 4: Responsive layout, keyboard accessibility and UI state refinement.
- Slice 5: Documentation, dependency hygiene and frontend maintainability.

# Out of scope
- Replay temps réel et connexion véhicule.
- Support complet BLF/MF4.
- Multi-bus avancé.
- Collaboration multi-utilisateur, cloud ou stockage partagé.
- Réécriture complète du frontend dans un framework.
- Packaging Windows natif, sauf décision séparée.

# Definition of Ready (DoR)
- [x] Problem statement is explicit and user impact is clear.
- [x] Scope boundaries (in/out) are explicit.
- [x] Acceptance criteria are testable.
- [x] Dependencies and known risks are listed.

# Dependencies and risks
- DuckDB, FastAPI, cantools et l'UI vanilla restent les composants cibles à court terme.
- Les traces/DBC réelles restent hors dépôt et ne doivent apparaître ni dans les fixtures,
  ni dans les logs CI, ni dans les caches versionnés.
- Les tests synthétiques doivent conserver les propriétés utiles des cas réels sans copier
  les données propriétaires ou sensibles.
- La comparaison structurelle des DBC doit inclure frame type, longueur, multiplexage,
  endianess, signedness, scale, offset, choices, unités et bornes pertinentes.
- Un cache persistant doit être invalidé par le contenu de la trace, des DBC, de la version
  de schéma et des décisions de résolution.
- La recommandation produit pour les jobs d'import est un état serveur temporaire par
  analyse, suffisant pour progression et annulation dans l'atelier local.
- La CSP peut rester compatible avec le frontend vanilla existant si le rendu texte sûr et
  les tests hostiles couvrent le risque prioritaire.
- Le support mobile complet n'est pas le cas d'usage principal ; le mode étroit doit au
  minimum garder les actions accessibles et ne pas masquer silencieusement le contenu.
- Les optimisations de concurrence DuckDB doivent préserver la stabilité acquise par le
  verrou de connexion actuel.

# Companion docs
- Product brief(s): `prod_002_product_brief_cantracediag_mvp`
- Architecture decision(s): `adr_002_adr_architecture_cantracediag_mvp`

# References
- `docs/audit-bout-en-bout-2026-07-15.md`
- `docs/product-backlog.md`
- `docs/roadmap.md`
- `req_001_ameliorer_mvp_cantracediag_analyse_diagnostic`
- `src/cantracediag/dbc.py`
- `src/cantracediag/decode.py`
- `src/cantracediag/pipeline.py`
- `src/cantracediag/store.py`
- `src/cantracediag/api.py`
- `src/cantracediag/web/index.html`
- `src/cantracediag/web/app.js`
- `.github/workflows/ci.yml`

# AI Context
- Summary: Harden CanTraceDiag after the 2026-07-15 end-to-end audit, starting with DBC
  correctness, safe UI rendering and reproducible CI, then disk-backed performance,
  diagnostic workflow completeness, responsive behavior and accessibility.
- Keywords: cantracediag, dbc-conflict, correctness, xss, duckdb, performance,
  responsive, accessibility, trace-filter, ci
- Use when: Planning or implementing post-MVP reliability, performance and UX hardening.
- Skip when: Work targets BLF/MF4, vehicle replay, cloud, collaboration or native Windows
  packaging.

# Backlog
- none
- `item_003_p0_retablir_la_confiance_dbc_la_securite_ui_et_la_ci`
- `item_004_p1_rendre_import_robuste_et_scalable`
- `item_005_p1_completer_le_workflow_diagnostic`
- `item_006_p1_rendre_interface_responsive_et_accessible`
- `item_007_p2_aligner_documentation_et_dependances`
