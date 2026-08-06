## req_019_publier_la_release_patch_v1_0_7_de_cantracediag - Publier la release patch v1.0.7 de CanTraceDiag
> From version: 1.0.7
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Complexity: Low
> Theme: Release
> Reminder: Update status/understanding/confidence and linked backlog/task references when you edit this doc.

# Needs
Publier une release patch `v1.0.7` de CanTraceDiag afin de déployer effectivement le rafraîchissement de l'emblème Paul Mondou servi en statique.

# Context
- La version précédente livrée était `1.0.6`.
- Le déploiement est déclenché exclusivement par un tag annoté `vX.Y.Z` sur `main`.
- Incrément patch retenu par l'opérateur, uniformément sur les six dépôts du portail.
- Doc rédigé en enregistrement rétroactif : la release était déjà publiée à la création de cette chaîne.

# Acceptance criteria
- AC1: La version passe de 1.0.6 à 1.0.7 dans toutes les surfaces canoniques du dépôt.
- AC2: Le commit de préparation est poussé sur `main` et le tag annoté `v1.0.7` pointe dessus.
- AC3: Le workflow release déclenché par le tag est vert de bout en bout (validate, publish, deploy, release).

# Definition of Ready (DoR)
- [x] Problem statement is explicit and user impact is clear.
- [x] Scope boundaries (in/out) are explicit.
- [x] Acceptance criteria are testable.
- [x] Dependencies and known risks are listed.

# Companion docs
- Product brief(s): (none yet)
- Architecture decision(s): (none yet)

# References
- `logics_manager/flow.py`
- `logics_manager/assist.py`
- `tests/python/test_logics_manager_cli.py`

# AI Context
- Summary: Draft a bounded request for publier la release patch v1.0.7 de cantracediag.
- Keywords: request-draft, logics-manager, python runtime, bundled CLI
- Use when: You need a new bounded request doc for the Logics workflow.
- Skip when: The work already has an existing request or should go straight to a backlog slice.

# Backlog
- none
- `item_037_publier_la_release_patch_v1_0_7_de_cantracediag`
