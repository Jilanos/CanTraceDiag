## item_028_p1_produire_le_dossier_de_preuve_go_no_go_hebergement - P1 produire le dossier de preuve go no go hebergement
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: Medium
> Theme: Release evidence
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- L audit demande de ne pas heberger tant que les preuves de correction et les limites residuelles ne sont pas explicites.
- Sans dossier de go/no-go, les anciennes taches Done peuvent etre interpretees a tort comme une readiness production.

# Scope
- In:
  - Regrouper les preuves de build, tests Python, tests navigateur, smoke Chromium et validation Logics.
  - Documenter les limites restantes : DBC non couvert, navigateurs non valides, performance/taille, migration workspaces et stockage local.
  - Mettre a jour la documentation de deploiement statique avec les preconditions minimales.
  - Produire une decision go/no-go datee pour cantracediag.paulmondou.fr.
- Out:
  - Effectuer le deploiement production.
  - Masquer des limites residuelles derriere une mention generique.
  - Clore task_021 si ses criteres larges OPFS/chunk/import restent ouverts.

# Acceptance criteria
- AC1: Un document de preuve post-audit liste les commandes executees, resultats, artefacts et references Logics.
- AC2: Les limites residuelles avant hebergement sont listees avec niveau de risque et decision.
- AC3: Le statut de task_021 est coherent avec ce qui reste hors gate hebergement.
- AC4: logics-manager lint --require-status et logics-manager audit --group-by-doc passent ou leurs anomalies sont classees.
- AC5: La decision go/no-go mentionne explicitement le domaine cible et la date.

# AC Traceability
- request-AC6 -> This backlog slice. Proof: AC1: Un document de preuve post-audit liste les commandes executees, resultats, artefacts et references Logics.
- request-AC2 -> This backlog slice. Evidence needed: Le produit FastAPI redevient un oracle fiable : /api/trace ne renvoie plus 500 au premier chargement, le middleware de securite accepte le contexte TestClient attendu, le code mort app.js contradictoire est retire ou neutralise, et la suite Python pertinente repasse au vert.
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
- Summary: P1 produire le dossier de preuve go no go hebergement
- Keywords: scaffolded-backlog, p1 produire le dossier de preuve go no go hebergement, implementation-ready
- Use when: Implementing the scaffolded slice for P1 produire le dossier de preuve go no go hebergement.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: Medium
- Rationale: Set by scaffold input or defaulted for grooming.

# Tasks
- `task_029_p1_produire_le_dossier_de_preuve_go_no_go_hebergement`

# Notes
- Task `task_029_p1_produire_le_dossier_de_preuve_go_no_go_hebergement` was finished via `logics-manager flow finish task` on 2026-07-22.
- Task `task_023_orchestrer_la_stabilisation_post_audit_full_frontend` was finished via `logics-manager flow finish task` on 2026-07-22.
