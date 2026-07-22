## item_023_p0_etablir_provenance_et_packaging_de_la_refonte_pwa - P0 etablir provenance et packaging de la refonte PWA
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: Medium
> Theme: Release provenance
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- L audit constate que la branche n a aucun commit d avance sur main et que l artefact deployable est un dossier de spike non suivi.
- Sans source versionnee ni generation reproductible, aucun deploiement public ne peut etre rattache a un etat controlable du projet.

# Scope
- In:
  - Identifier les fichiers sources et generes de la refonte PWA a suivre ou a exclure.
  - Separer clairement les changements FastAPI, la promotion PWA et les artefacts buildes dans la strategie de commit.
  - Documenter la commande de build et la relation entre sources, site genere et hebergement cible.
  - Mettre a jour task_021 pour referencer cette chaine comme gate avant fermeture MVP.
- Out:
  - Forcer un commit Git automatique.
  - Deployer sur le domaine public.
  - Refondre l architecture PWA au-dela du packaging/provenance.

# Acceptance criteria
- AC1: Un inventaire commit/source/build precise quels fichiers sont sources, generes, temporaires ou a ignorer.
- AC2: La refonte est separable en lots commit-ready au minimum FastAPI oracle, PWA source et documentation/preuves.
- AC3: Le build statique est reproductible depuis les sources suivies par une commande documentee.
- AC4: task_021 reference explicitement cette chaine comme dependance de fermeture post-audit.
- AC5: La validation Logics confirme que les nouveaux liens de chaine sont coherents.

# AC Traceability
- request-AC1 -> This backlog slice. Proof: AC1: Un inventaire commit/source/build precise quels fichiers sont sources, generes, temporaires ou a ignorer.
- request-AC6 -> This backlog slice. Proof: AC2: La refonte est separable en lots commit-ready au minimum FastAPI oracle, PWA source et documentation/preuves.
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
- Summary: P0 etablir provenance et packaging de la refonte PWA
- Keywords: scaffolded-backlog, p0 etablir provenance et packaging de la refonte pwa, implementation-ready
- Use when: Implementing the scaffolded slice for P0 etablir provenance et packaging de la refonte PWA.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: High
- Rationale: Set by scaffold input or defaulted for grooming.

# Tasks
- `task_024_p0_etablir_provenance_et_packaging_de_la_refonte_pwa`

# Notes
- Task `task_024_p0_etablir_provenance_et_packaging_de_la_refonte_pwa` was finished via `logics-manager flow finish task` on 2026-07-22.
- Task `task_023_orchestrer_la_stabilisation_post_audit_full_frontend` was finished via `logics-manager flow finish task` on 2026-07-22.
