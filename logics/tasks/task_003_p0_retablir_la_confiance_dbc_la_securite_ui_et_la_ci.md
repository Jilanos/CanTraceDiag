## task_003_p0_retablir_la_confiance_dbc_la_securite_ui_et_la_ci - P0 Retablir la confiance DBC la securite UI et la CI
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: Medium
> Theme: Implementation delivery
> Reminder: Update status/understanding/confidence/progress and linked request/backlog references when you edit this doc.
> Owner: codex

# Definition of Done (DoD)
- [x] The backlog scope is implemented.
- [x] Acceptance criteria are covered.
- [x] Validation passes.
- [x] Meaningful waves followed ADR 009: affected docs updated and the repo left commit-ready without automatic commits.

# Backlog
- `item_003_p0_retablir_la_confiance_dbc_la_securite_ui_et_la_ci`

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

# Implementation approach
- Centraliser la comparaison structurelle DBC et couvrir frame type, longueur,
  multiplexage, endianess, signedness, scale, offset, choices, unités et bornes utiles.
- Ajouter les fixtures synthétiques de conflits `0x710` et `0x720` à `0x725`.
- Faire continuer l'import des frames non ambiguës et présenter les choix ambigus dans une
  pop-up validée côté API.
- Remplacer les rendus `innerHTML` exposés par des écritures texte ou des constructions DOM
  sûres, puis ajouter le test hostile.
- Corriger la CI pour installer les extras nécessaires et exécuter le jeu de validation P0.

# Validation
- Run `python3 -m logics_manager lint --require-status`.
- Use `python3 -m logics_manager flow progress task task_003_p0_retablir_la_confiance_dbc_la_securite_ui_et_la_ci.md --progress <n>%` during multi-wave work.
- Run `python3 -m logics_manager flow finish task task_003_p0_retablir_la_confiance_dbc_la_securite_ui_et_la_ci.md` after implementation.
- `.venv/bin/ruff check .` passed.
- `.venv/bin/pytest` passed: 54 passed, 1 warning.
- `logics-manager lint --require-status` passed.
- `logics-manager audit --group-by-doc` is non-blocking with deferred warnings for AC6-AC16, which belong to later slices.
- Finish workflow executed on 2026-07-15.
- Linked backlog/request close verification passed.

# Report
- Implemented DBC conflict detection/resolution, safe rendering and CI repair as one P0
- Finished on 2026-07-15.
- Linked backlog item(s): `item_003_p0_retablir_la_confiance_dbc_la_securite_ui_et_la_ci`
- Related request(s): `req_002_fiabiliser_cantracediag_apres_audit_fonctionnel_ui_et_performance`
  delivery block.
- Closeout is intentionally deferred because the parent request still includes open
  AC6-AC16 slices.

# AI Context
- Summary: Implement DBC conflict detection/resolution, safe rendering and CI repair as
  one P0 delivery block.
- Keywords: task, implementation, backlog, runtime, python
- Use when: You need a bounded implementation task for a backlog item.
- Skip when: The work is still at the request or backlog shaping stage.

# Links
- Request: `req_002_fiabiliser_cantracediag_apres_audit_fonctionnel_ui_et_performance`
- Product brief(s): (none yet)
- Architecture decision(s): (none yet)

# AC Traceability
- request-AC1 -> This task. Proof: `tests/test_dbc_decode.py` covers differing same-name duplicates and equivalent duplicate auto-acceptance.
- request-AC2 -> This task. Proof: `tests/test_diagnostic.py` covers conflict pop-up API flow, choice validation, persistence and trace exposure.
- request-AC3 -> This task. Proof: synthetic DBC conflict fixtures cover deterministic decoding before and after operator resolution.
- request-AC4 -> This task. Proof: CSP is present and `tests/test_e2e_ui.py::test_imported_text_does_not_execute_html` proves hostile ASC/DBC text does not execute.
- request-AC5 -> This task. Proof: CI installs `.[api,dev]`; `.venv/bin/ruff check .` and `.venv/bin/pytest` pass locally.
