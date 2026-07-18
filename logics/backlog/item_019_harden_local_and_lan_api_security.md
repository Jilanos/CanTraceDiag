## item_019_harden_local_and_lan_api_security - Harden local and LAN API security
> From version: 0.1.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: High
> Theme: Operator workflow and runtime integration
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
L'API locale ne controle pas encore Host, Origin, token ou taille d'upload. En mode
LAN, l'import par chemin pourrait transformer le service en lecteur de fichiers du
poste. Le mode local doit rester simple et le mode LAN explicitement protege.

# Scope
- In:
  - allowlist Host, controle Origin et taille maximale configurable des uploads
  - token sur les mutations locales et sur toute l'API en mode LAN
  - desactivation de l'import par chemin en mode LAN
  - messages sans fuite de chemins et tests hostiles
- Out:
  - authentification multi-utilisateur et gestion de comptes
  - exposition cloud ou Internet

# Acceptance criteria
- AC10: L'API rejette un Host ou une Origin non autorises, exige un jeton de session
- AC11: L'import par chemin serveur est desactive hors boucle locale ou derriere une

# AC Traceability
- request-AC10 -> This backlog slice. Proof: AC10: L'API rejette un Host ou une Origin non autorises, exige un jeton de session
- request-AC11 -> This backlog slice. Proof: AC11: L'import par chemin serveur est desactive hors boucle locale ou derriere une

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
- Request: `logics/request/req_007_finaliser_workflow_diagnostic_et_clarifier_cantracediag.md`
- Primary task(s): (none yet)

# AI Context
- Summary: Harden local and LAN API security
- Keywords: backlog-groom, request, harden local and lan api security, bounded slice
- Use when: Use when implementing or reviewing the delivery slice for Harden local and LAN API security.
- Skip when: Skip when the change is unrelated to this delivery slice or its linked request.

# Priority
- Priority: High
- Rationale: La lecture de fichiers et le mode LAN constituent une frontiere de securite P0.

# Notes
- Hybrid rationale: Derived from request `req_007_finaliser_workflow_diagnostic_et_clarifier_cantracediag` and kept bounded to one coherent delivery slice.
- Source file: `logics/request/req_007_finaliser_workflow_diagnostic_et_clarifier_cantracediag.md`.
- Generated locally by logics-manager.
- Task `task_019_harden_local_and_lan_api_security` was finished via `logics-manager flow finish task` on 2026-07-18.

# Tasks
- `task_019_harden_local_and_lan_api_security`
