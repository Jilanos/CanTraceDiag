## req_016_ajouter_le_lien_parent_et_la_version_dans_la_top_barre - Ajouter le lien parent et la version dans la top barre
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Complexity: Medium
> Theme: General
> Reminder: Update status/understanding/confidence and linked backlog/task references when you edit this doc.

# Needs
- Ajouter dans la top barre de CanTraceDiag un acces explicite au site parent
  `paulmondou.fr`, represente par l'embleme Paul Mondou fourni localement.
- Afficher le numero de version applicative dans cette meme top barre afin que
  l'operateur identifie immediatement la version executee.
- Livrer le changement avec la politique classique de deploiement du depot :
  validation locale, preparation de version, commit, push, CI, tag annote et
  verification de release lorsque les preconditions git/CI sont reunies.

# Context
- Source d'asset fournie par l'operateur :
  `/home/paul/dev/WORK/perso/Icones/paulmondou`.
- Destination fonctionnelle : top barre de l'interface web/PWA CanTraceDiag.
- Le lien parent doit pointer vers `https://paulmondou.fr/`.
- Le numero de version doit provenir d'une surface canonique du projet, sans
  duplication manuelle fragile.

# Acceptance criteria
- AC1: La top barre expose un lien visible et accessible vers
  `https://paulmondou.fr/`, rendu avec l'embleme Paul Mondou fourni.
- AC2: L'embleme est integre comme asset applicatif versionne, avec dimensions
  stables et alternative accessible.
- AC3: La top barre affiche le numero de version courant de CanTraceDiag depuis
  une source canonique du depot.
- AC4: Le changement reste borne a la top barre, aux assets necessaires, a la
  propagation de version et aux validations/deploiement associes.
- AC5: La livraison suit la politique classique du depot et laisse des preuves
  explicites de validation, commit/version, CI/tag/release ou des blocages
  externes constates.

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
- Summary: Draft a bounded request for ajouter le lien parent et la version dans la top barre.
- Keywords: request-draft, logics-manager, python runtime, bundled CLI
- Use when: You need a new bounded request doc for the Logics workflow.
- Skip when: The work already has an existing request or should go straight to a backlog slice.

# Backlog
- none
- `item_033_ajouter_le_lien_parent_et_la_version_dans_la_top_barre`
