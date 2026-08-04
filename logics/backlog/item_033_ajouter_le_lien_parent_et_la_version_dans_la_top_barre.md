## item_033_ajouter_le_lien_parent_et_la_version_dans_la_top_barre - Ajouter le lien parent et la version dans la top barre
> From version: 1.0.0
> Schema version: 1.0
> Status: In progress
> Understanding: 90%
> Confidence: 85%
> Progress: 80%
> Complexity: High
> Theme: Operator workflow and runtime integration
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
Les operateurs ne disposent pas aujourd'hui d'un repere immediat dans la top
barre pour revenir au site parent `paulmondou.fr` ni pour identifier la version
exacte de CanTraceDiag en cours d'utilisation. Cela complique le support, la
qualification et la verification apres deploiement.

# Scope
- In:
  - integration de l'embleme Paul Mondou fourni dans les assets web/PWA
  - ajout du lien parent `https://paulmondou.fr/` dans la top barre
  - affichage de la version courante dans la top barre depuis une source
    canonique du projet
  - validation locale et preparation de la livraison selon la politique de
    deploiement classique
- Out:
  - refonte globale de navigation
  - changement d'identite visuelle hors embleme demande
  - modification fonctionnelle du diagnostic CAN
  - deploiement manuel hors processus git/CI/tag existant

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

# AC Traceability
- request-AC1 -> This backlog slice. Proof: backlog AC1 covers the parent link and emblem.
- request-AC2 -> This backlog slice. Proof: backlog AC2 covers versioned app assets and accessibility.
- request-AC3 -> This backlog slice. Proof: backlog AC3 covers canonical version display.
- request-AC4 -> This backlog slice. Proof: scope keeps work bounded to top bar, asset, version and delivery.
- request-AC5 -> This backlog slice. Proof: backlog AC5 and AC6 cover validation and deployment evidence.

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
- Request: `logics/request/req_016_ajouter_le_lien_parent_et_la_version_dans_la_top_barre.md`
- Primary task(s): (none yet)

# AI Context
- Summary: Ajouter le lien parent et la version dans la top barre
- Keywords: backlog-groom, request, ajouter le lien parent et la version dans la top barre, bounded slice
- Use when: Use when implementing or reviewing the delivery slice for Ajouter le lien parent et la version dans la top barre.
- Skip when: Skip when the change is unrelated to this delivery slice or its linked request.

# Priority
- Priority: Medium
- Rationale: The change improves supportability and release identification but
  does not block diagnostic execution.

# Notes
- Hybrid rationale: Derived from request `req_016_ajouter_le_lien_parent_et_la_version_dans_la_top_barre` and kept bounded to one coherent delivery slice.
- Source file: `logics/request/req_016_ajouter_le_lien_parent_et_la_version_dans_la_top_barre.md`.
- Generated locally by logics-manager.

# Tasks
- `task_035_ajouter_le_lien_parent_et_la_version_dans_la_top_barre`
