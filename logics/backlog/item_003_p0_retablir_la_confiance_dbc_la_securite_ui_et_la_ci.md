## item_003_p0_retablir_la_confiance_dbc_la_securite_ui_et_la_ci - P0 Retablir la confiance DBC la securite UI et la CI
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: High
> Theme: Operator workflow and runtime integration
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.
> Owner: codex

# Problem
Le diagnostic ne peut pas être fiable tant que deux DBC peuvent définir le même arbitration
ID sans détection exhaustive, que l'ordre d'upload peut influencer silencieusement le
décodage, que les champs ASC/DBC peuvent injecter du HTML dans l'interface et que la CI ne
reproduit pas l'environnement de test réel.

# Scope
- In:
  - détection exhaustive des conflits DBC, y compris noms de messages identiques
  - empreinte canonique des définitions DBC pour auto-accepter seulement les équivalences
  - import en arrière-plan des frames non ambiguës et pop-up de confirmation des choix
    ambigus
  - persistance et exposition des décisions DBC dans rapport d'import et inspecteur
  - rendu DOM sûr des données ASC/DBC, CSP pragmatique et test hostile
  - CI reproductible installant les extras nécessaires et lançant lint, API et E2E
- Out:
  - migration frontend complète ou suppression obligatoire de tout `unsafe-inline`
  - optimisation volumétrique DuckDB hors corrections nécessaires au P0
  - intégration de traces ou DBC réelles dans le dépôt

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

# AC Traceability
- request-AC1 -> This backlog slice. Proof: conflict detection and canonical equivalence.
- request-AC2 -> This backlog slice. Proof: exhaustive operator-confirmed DBC resolution.
- request-AC3 -> This backlog slice. Proof: deterministic decoding with synthetic conflict fixtures.
- request-AC4 -> This backlog slice. Proof: text rendering, CSP and hostile HTML/JS test.
- request-AC5 -> This backlog slice. Proof: clean CI install and API/E2E/lint execution.

# Delivery notes
- Livrer ce lot P0 comme un seul bloc cohérent.
- Ne jamais intégrer les fichiers DBC réels : reproduire leurs formes de conflit par
  fixtures synthétiques.
- Préserver l'analyse précédente jusqu'à validation complète du nouvel import.

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
- Primary task(s): `task_003_p0_retablir_la_confiance_dbc_la_securite_ui_et_la_ci`

# AI Context
- Summary: Restore diagnostic trust by fixing DBC arbitration conflicts, safe UI rendering
  and reproducible CI as one P0 block.
- Keywords: backlog-groom, request, p0 retablir la confiance dbc la securite ui et la ci, bounded slice
- Use when: Use when implementing or reviewing the delivery slice for P0 Retablir la confiance DBC la securite UI et la CI.
- Skip when: Skip when the change is unrelated to this delivery slice or its linked request.

# Priority
- Priority: High
- Rationale: La justesse du décodage, l'injection HTML et la CI conditionnent toute
  utilisation fiable des autres fonctions.

# Notes
- Hybrid rationale: Derived from request `req_002_fiabiliser_cantracediag_apres_audit_fonctionnel_ui_et_performance` and kept bounded to one coherent delivery slice.
- Source file: `logics/request/req_002_fiabiliser_cantracediag_apres_audit_fonctionnel_ui_et_performance.md`.
- Generated locally by logics-manager.
- Task `task_003_p0_retablir_la_confiance_dbc_la_securite_ui_et_la_ci` was finished via `logics-manager flow finish task` on 2026-07-15.

# Tasks
- `task_003_p0_retablir_la_confiance_dbc_la_securite_ui_et_la_ci`
