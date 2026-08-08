## item_038_remplacer_les_assets_web_et_l_ico_cantracediag - Remplacer les assets web et l'ICO CanTraceDiag
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 95%
> Confidence: 92%
> Progress: 100%
> Complexity: High
> Theme: Brand asset integration
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- L'icone, l'embleme et l'ICO proviennent d'un lot errone.

# Scope
- In:
  - `web/app-icon.svg` et `web/app-emblem.svg` depuis `a black/SVG upgraded/cantracediag-emblem-dark.svg`
  - `web/paulmondou-emblem.svg` depuis `a black/SVG upgraded/paulmondou-emblem.svg`
  - `web/app-icon.ico` regenere depuis le master SVG (16/32/48/64/128/256)
  - Retrait des PNG d'identite orphelins de `src/cantracediag/web/`
  - Mise a jour des references et des types dans `web/index.html`, `pyproject.toml` et la chaine PWA (`build-browser.mjs`, `manifest.webmanifest`, `sw.js`)
- Out:
  - Modifier les captures de `docs/assets/`.
  - Ajouter un fond, une plaque de couleur ou un cartouche derriere un asset transparent.

# Acceptance criteria
- AC1: Les trois SVG servis sont les masters `SVG upgraded`, octet pour octet; l'ICO et les icones PWA 192/512 en derivent.
- AC2: `web/index.html`, le manifest et le service worker referencent ces assets avec le bon type MIME, sans reference cassee.
- AC3: Favicon et embleme s'affichent correctement sur le fond sombre.

# AC Traceability
- request-AC1 -> This backlog slice. Proof: AC1: Les trois PNG et l'ICO derivent des masters attendus.
- request-AC2 -> This backlog slice. Proof: AC2: `web/index.html` et `api.py` ne referencent plus de SVG pour ces assets.
- request-AC3 -> This backlog slice. Proof: AC3: Favicon et embleme s'affichent correctement sur le fond sombre.
- request-AC4 -> This backlog slice. Proof: AC3: Favicon et embleme s'affichent correctement sur le fond sombre.
- request-AC5 -> This backlog slice. Evidence needed: La livraison se termine par un commit de version X.Y.Z+1, un push, puis un tag annote vX.Y.Z+1 dont le workflow release est vert.

# Decision framing
- Product framing: Not needed
- Architecture framing: Not needed

# Links
- Product brief(s): `prod_007_identite_cantracediag_alignee_sur_icones_v3_corrige`
- Architecture decision(s): (none yet)
- Request: `req_020_remplacer_les_assets_cantracediag_par_les_masters_icones_v3_corriges`
- Primary task(s): `task_039_remplacer_les_assets_cantracediag_par_les_masters_icones_v3_corriges`

# AI Context
- Summary: Remplacer les assets web et l'ICO CanTraceDiag
- Keywords: scaffolded-backlog, remplacer les assets web et l'ico cantracediag, implementation-ready
- Use when: Implementing the scaffolded slice for Remplacer les assets web et l'ICO CanTraceDiag.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: High
- Rationale: Set by scaffold input or defaulted for grooming.

# Tasks
- `task_039_remplacer_les_assets_cantracediag_par_les_masters_icones_v3_corriges`

# Notes
- Task `task_039_remplacer_les_assets_cantracediag_par_les_masters_icones_v3_corriges` was finished via `logics-manager flow finish task` on 2026-08-08.
