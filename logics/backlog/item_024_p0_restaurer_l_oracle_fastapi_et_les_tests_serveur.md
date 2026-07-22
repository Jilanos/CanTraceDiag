## item_024_p0_restaurer_l_oracle_fastapi_et_les_tests_serveur - P0 restaurer l oracle FastAPI et les tests serveur
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: Medium
> Theme: Backend regression recovery
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- /api/trace passe cursor en argument positionnel offset et renvoie 500 au premier chargement.
- Le middleware security.py rejette Host: testserver, ce qui masque les tests de bout en bout des nouvelles features.
- src/cantracediag/web/app.js contient du code mort modifie, casse et non charge par index.html.

# Scope
- In:
  - Corriger le contrat de pagination trace pour cursor/offset/start_index/next_cursor/prev_cursor.
  - Adapter la configuration de securite afin que TestClient reste couvert sans affaiblir la posture locale.
  - Supprimer, neutraliser ou documenter clairement app.js comme legacy si le front modulaire js/*.js est la source active.
  - Ajouter ou ajuster les tests HTTP pour /api/trace, /api/cursors, export csv_wide et les gardes securite.
- Out:
  - Changer l UX PWA navigateur.
  - Remplacer FastAPI par le moteur navigateur.
  - Assouplir globalement Host/Origin sans tests de regression.

# Acceptance criteria
- AC1: GET /api/trace au premier chargement retourne 200 et une reponse conforme au contrat attendu par trace.js.
- AC2: Les tests couvrent explicitement Host: testserver et les refus Host/Origin non autorises.
- AC3: Les tests HTTP couvrent /api/cursors, /api/export en csv_wide et la forme keyset de /api/trace.
- AC4: Le code mort app.js contradictoire ne peut plus etre confondu avec le front actif.
- AC5: La suite Python pertinente repasse au vert ou liste seulement des echecs residuels non lies avec justification.

# AC Traceability
- request-AC2 -> This backlog slice. Proof: AC1: GET /api/trace au premier chargement retourne 200 et une reponse conforme au contrat attendu par trace.js.
- request-AC6 -> This backlog slice. Proof: AC2: Les tests couvrent explicitement Host: testserver et les refus Host/Origin non autorises.
- request-AC3 -> This backlog slice. Evidence needed: Le moteur navigateur atteint la parite minimale trace reelle avec l oracle Python pour IDs etendus 29 bits, signaux Motorola/big-endian et multiplexage DBC, avec fixtures de regression representatives.
- request-AC4 -> This backlog slice. Evidence needed: Les divergences fonctionnelles restantes du moteur navigateur sont soit corrigees soit documentees avec decision explicite : locateRow, DBC dupliques, parsing ASC strict, filtres trace_rows, decimation signalSeries, contrat signalStats et limites de decode_error.
- request-AC5 -> This backlog slice. Evidence needed: Le cycle de vie PWA est deployable : service worker actualisable, strategie de cache coherente avec les noms d assets, garde de quota pour les DBC/workspaces et manifest avec icones raster 192 et 512.

# Decision framing
- Product framing: Not needed
- Architecture framing: Not needed

# Links
- Product brief(s): `prod_003_gate_d_hebergement_pwa_full_frontend_post_audit`
- Architecture decision(s): (none yet)
- Request: `req_013_lever_les_bloquants_d_hebergement_pwa_full_frontend_post_audit_2026_07_22`
- Primary task(s): `task_023_orchestrer_la_stabilisation_post_audit_full_frontend`

# AI Context
- Summary: P0 restaurer l oracle FastAPI et les tests serveur
- Keywords: scaffolded-backlog, p0 restaurer l oracle fastapi et les tests serveur, implementation-ready
- Use when: Implementing the scaffolded slice for P0 restaurer l oracle FastAPI et les tests serveur.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: High
- Rationale: Set by scaffold input or defaulted for grooming.

# Tasks
- `task_025_p0_restaurer_l_oracle_fastapi_et_les_tests_serveur`

# Notes
- Task `task_025_p0_restaurer_l_oracle_fastapi_et_les_tests_serveur` was finished via `logics-manager flow finish task` on 2026-07-22.
- Task `task_023_orchestrer_la_stabilisation_post_audit_full_frontend` was finished via `logics-manager flow finish task` on 2026-07-22.
