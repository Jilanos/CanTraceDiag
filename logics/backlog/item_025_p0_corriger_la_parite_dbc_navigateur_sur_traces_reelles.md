## item_025_p0_corriger_la_parite_dbc_navigateur_sur_traces_reelles - P0 corriger la parite DBC navigateur sur traces reelles
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: High
> Theme: Browser engine parity
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- Le moteur navigateur ne decode pas les IDs etendus 29 bits car il conserve le bit DBC et force is_extended_id a false.
- Les signaux Motorola big-endian provoquent decode_error et perdent toute la frame.
- Le multiplexage DBC est parse puis ignore, ce qui emet des signaux absents avec des valeurs fausses.

# Scope
- In:
  - Aligner le parsing DBC navigateur sur l oracle Python pour IDs standard/etendus.
  - Implementer l extraction Motorola/big-endian compatible cantools sur les cas couverts par fixtures.
  - Conserver et appliquer les informations multiplexeur M et m<n> pendant le decode.
  - Ajouter des fixtures ASC/DBC de regression J1939 29 bits, Motorola et multiplexage.
  - Comparer les sorties navigateur a l oracle Python dans les tests de parite.
- Out:
  - Supporter toute la grammaire DBC non citee par l audit.
  - Optimiser les performances gros fichiers.
  - Modifier le contrat public sans migration explicite.

# Acceptance criteria
- AC1: Une frame J1939/29 bits representative est decodee cote navigateur avec le meme message et les memes signaux que l oracle Python.
- AC2: Un signal Motorola/big-endian fixture est decode sans decode_error et avec valeur numerique alignee sur l oracle.
- AC3: Un message multiplexe n expose que les signaux correspondant a la valeur de multiplexeur active.
- AC4: Les tests de parite echouent en cas de regression des trois bloquants.
- AC5: Les limites DBC encore non couvertes sont documentees dans les preuves de la tache.

# AC Traceability
- request-AC3 -> This backlog slice. Proof: AC1: Une frame J1939/29 bits representative est decodee cote navigateur avec le meme message et les memes signaux que l oracle Python.
- request-AC6 -> This backlog slice. Proof: AC2: Un signal Motorola/big-endian fixture est decode sans decode_error et avec valeur numerique alignee sur l oracle.
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
- Summary: P0 corriger la parite DBC navigateur sur traces reelles
- Keywords: scaffolded-backlog, p0 corriger la parite dbc navigateur sur traces reelles, implementation-ready
- Use when: Implementing the scaffolded slice for P0 corriger la parite DBC navigateur sur traces reelles.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: High
- Rationale: Set by scaffold input or defaulted for grooming.

# Tasks
- `task_026_p0_corriger_la_parite_dbc_navigateur_sur_traces_reelles`

# Notes
- Task `task_026_p0_corriger_la_parite_dbc_navigateur_sur_traces_reelles` was finished via `logics-manager flow finish task` on 2026-07-22.
- Task `task_023_orchestrer_la_stabilisation_post_audit_full_frontend` was finished via `logics-manager flow finish task` on 2026-07-22.
