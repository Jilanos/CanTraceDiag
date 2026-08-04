## task_035_ajouter_le_lien_parent_et_la_version_dans_la_top_barre - Ajouter le lien parent et la version dans la top barre
> From version: 1.0.0
> Schema version: 1.0
> Status: In progress
> Understanding: 90%
> Confidence: 85%
> Progress: 80%
> Complexity: Medium
> Theme: Implementation delivery
> Reminder: Update status/understanding/confidence/progress and linked request/backlog references when you edit this doc.
> Owner: codex

# Definition of Done (DoD)
- [ ] The backlog scope is implemented.
- [ ] Acceptance criteria are covered.
- [ ] Validation passes.
- [ ] Meaningful waves followed ADR 009: affected docs updated and the repo left commit-ready without automatic commits.

# Backlog
- `item_033_ajouter_le_lien_parent_et_la_version_dans_la_top_barre`

# Acceptance criteria
- AC1: La top barre contient un lien accessible vers `https://paulmondou.fr/`
  dont le contenu visuel utilise l'embleme Paul Mondou fourni.
- AC2: L'embleme est copie dans les assets applicatifs versionnes et reference
  par l'interface sans dependance au chemin local externe de l'operateur.
- AC3: La top barre affiche le numero de version de CanTraceDiag et cette valeur
  provient d'une surface canonique synchronisee avec la version release.
- AC4: Les dimensions et etats responsives de la top barre restent stables sur
  desktop et mobile.
- AC5: La validation locale couvre le rendu web/PWA pertinent et la coherence
  de version.
- AC6: La livraison applique la sequence classique du depot : validation locale,
  commit d'implementation, preparation SemVer, commit de version, push, attente
  CI, tag annote `vX.Y.Z`, verification release, ou consigne un blocage externe.

# Plan
- [ ] Identifier la top barre, la surface de version canonique et le chemin de
  build/deploiement du projet.
- [ ] Copier l'embleme Paul Mondou adapte dans les assets versionnes.
- [ ] Ajouter le lien parent et la version dans la top barre avec rendu stable.
- [ ] Valider localement le rendu et la coherence de version.
- [ ] Executer la politique classique de deploiement ou documenter le blocage
  externe exact.
- [ ] Run `python3 -m logics_manager flow finish task task_035_ajouter_le_lien_parent_et_la_version_dans_la_top_barre.md` after implementation.

# Validation
- Planned:
  - `python -m pytest`
  - web/PWA smoke or build command identified from the repository
  - `logics-manager lint --require-status`
  - `logics-manager audit --legacy-cutoff-version 1.1.0 --group-by-doc`

# Report
- Started from operator request on 2026-08-04.

# AI Context
- Summary: Implement ajouter le lien parent et la version dans la top barre.
- Keywords: task, implementation, backlog, runtime, python
- Use when: You need a bounded implementation task for a backlog item.
- Skip when: The work is still at the request or backlog shaping stage.

# Links
- Request: `req_016_ajouter_le_lien_parent_et_la_version_dans_la_top_barre`
- Product brief(s): (none yet)
- Architecture decision(s): (none yet)
