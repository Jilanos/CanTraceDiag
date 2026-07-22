## item_026_p1_aligner_les_divergences_moteur_navigateur_non_bloquantes - P1 aligner les divergences moteur navigateur non bloquantes
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: High
> Theme: Behavioral parity
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- Plusieurs ecarts moyens peuvent produire des resultats divergents sans etre les premiers bloquants d hebergement.
- Ces ecarts concernent locateRow, DBC dupliques, parsing ASC permissif, filtres trace_rows, signalSeries, signalStats et decode_error.

# Scope
- In:
  - Corriger locateRow pour retourner la ligne temporellement la plus proche comme l oracle Python.
  - Decoder les DBC dupliques identiques au lieu de produire unknown_id.
  - Rendre le parsing ASC aussi strict que l oracle pour IDs et octets malformes.
  - Aligner les filtres trace_rows principaux : events, id_hex, casse et sous-chaines.
  - Aligner ou documenter signalSeries, signalStats et les criteres decode_error.
- Out:
  - Bloquer la correction des P0 si cette tranche prend du retard.
  - Changer l interface utilisateur au-dela des effets de contrat necessaires.
  - Atteindre une equivalence bit a bit sur des cas DBC non couverts.

# Acceptance criteria
- AC1: Chaque divergence listee par l audit a un test, une correction ou une decision de report documentee.
- AC2: locateRow retourne une ligne non nulle quand la trace contient des lignes et selectionne le timestamp le plus proche.
- AC3: Deux DBC identiques charges ensemble ne rendent pas les frames correspondantes unknown_id.
- AC4: Le contrat signalStats navigateur expose les noms attendus ou une adaptation consommatrice testee.
- AC5: Les reports residuels sont visibles dans la documentation pre-hebergement.

# AC Traceability
- request-AC4 -> This backlog slice. Proof: AC1: Chaque divergence listee par l audit a un test, une correction ou une decision de report documentee.
- request-AC6 -> This backlog slice. Proof: AC2: locateRow retourne une ligne non nulle quand la trace contient des lignes et selectionne le timestamp le plus proche.
- request-AC3 -> This backlog slice. Evidence needed: Le moteur navigateur atteint la parite minimale trace reelle avec l oracle Python pour IDs etendus 29 bits, signaux Motorola/big-endian et multiplexage DBC, avec fixtures de regression representatives.
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
- Summary: P1 aligner les divergences moteur navigateur non bloquantes
- Keywords: scaffolded-backlog, p1 aligner les divergences moteur navigateur non bloquantes, implementation-ready
- Use when: Implementing the scaffolded slice for P1 aligner les divergences moteur navigateur non bloquantes.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: Medium
- Rationale: Set by scaffold input or defaulted for grooming.

# Tasks
- `task_027_p1_aligner_les_divergences_moteur_navigateur_non_bloquantes`

# Notes
- Task `task_027_p1_aligner_les_divergences_moteur_navigateur_non_bloquantes` was finished via `logics-manager flow finish task` on 2026-07-22.
- Task `task_023_orchestrer_la_stabilisation_post_audit_full_frontend` was finished via `logics-manager flow finish task` on 2026-07-22.
