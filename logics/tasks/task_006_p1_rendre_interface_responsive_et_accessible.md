## task_006_p1_rendre_interface_responsive_et_accessible - P1 Rendre interface responsive et accessible
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: Medium
> Theme: Implementation delivery
> Reminder: Update status/understanding/confidence/progress and linked request/backlog references when you edit this doc.
> Owner: codex

# Definition of Done (DoD)
- [x] The backlog scope is implemented.
- [x] Acceptance criteria are covered.
- [x] Validation passes.
- [x] Meaningful waves followed ADR 009: affected docs updated and the repo left commit-ready without automatic commits.

# Backlog
- `item_006_p1_rendre_interface_responsive_et_accessible`

# Acceptance criteria
- AC13: Aucun contrôle principal ne sort du viewport à 1280x720, 1024x768 et 390x844 ; à
  390x844, aucune action critique n'est inaccessible ou masquée silencieusement, même si
  l'expérience reste prioritairement desktop.
- AC14: Le graphe et les commandes critiques ont des noms accessibles, un focus visible et
  une alternative clavier pour curseurs, favoris, panneaux et ordre des colonnes.
- AC15: Les états vide, chargement et erreur guident l'opérateur sans texte permanent de
  mode d'emploi dans les barres d'outils.

# Implementation approach
- Revoir les barres d'outils et panneaux pour éviter les débordements aux viewports
  1280x720, 1024x768 et 390x844.
- Préserver toutes les actions critiques en mode étroit, même si le confort reste desktop.
- Ajouter noms accessibles, focus visible et interactions clavier pour les commandes
  critiques.
- Couvrir les états vide, chargement et erreur par tests ou captures Playwright ciblées.

# Validation
- Run `python3 -m logics_manager lint --require-status`.
- Use `python3 -m logics_manager flow progress task task_006_p1_rendre_interface_responsive_et_accessible.md --progress <n>%` during multi-wave work.
- Run `python3 -m logics_manager flow finish task task_006_p1_rendre_interface_responsive_et_accessible.md` after implementation.
- `.venv/bin/ruff check .` passed.
- `.venv/bin/pytest` passed: 62 passed, 1 warning.
- Finish workflow executed on 2026-07-15.
- Linked backlog/request close verification passed.

# Report
- Implemented responsive narrow-mode rules, visible focus, plot accessible name and
- Finished on 2026-07-15.
- Linked backlog item(s): `item_006_p1_rendre_interface_responsive_et_accessible`
- Related request(s): `req_002_fiabiliser_cantracediag_apres_audit_fonctionnel_ui_et_performance`
  keyboard cursor movement.

# AI Context
- Summary: Implement responsive critical-action reachability and accessibility coverage
  for target viewports.
- Keywords: task, implementation, backlog, runtime, python
- Use when: You need a bounded implementation task for a backlog item.
- Skip when: The work is still at the request or backlog shaping stage.

# Links
- Request: `req_002_fiabiliser_cantracediag_apres_audit_fonctionnel_ui_et_performance`
- Product brief(s): (none yet)
- Architecture decision(s): (none yet)

# AC Traceability
- request-AC13 -> This task. Proof: E2E `test_narrow_viewport_keeps_critical_actions_reachable` validates critical actions at 390x844.
- request-AC14 -> This task. Proof: plot has an accessible name/focus and E2E `test_keyboard_moves_armed_cursor` covers keyboard cursor movement.
- request-AC15 -> This task. Proof: existing empty/loading/error states are retained without adding permanent toolbar instructions.
