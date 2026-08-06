## item_038_remplacer_les_assets_web_et_l_ico_cantracediag - Remplacer les assets web et l'ICO CanTraceDiag
> From version: 1.0.0
> Schema version: 1.0
> Status: Ready
> Understanding: 90%
> Confidence: 85%
> Progress: 0%
> Complexity: High
> Theme: Brand asset integration
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- L'icone, l'embleme et l'ICO proviennent d'un lot errone.

# Scope
- In:
  - `web/app-icon.svg` -> `app-icon.png` depuis `cantracediag/cantracediag-icon-dark.png`
  - `web/app-emblem.svg` -> `app-emblem.png` depuis `cantracediag/cantracediag-emblem-dark.png`
  - `web/app-icon.ico` regenere depuis `cantracediag/cantracediag-icon-dark.png`
  - `web/paulmondou-emblem.png` depuis `paulmondou/paulmondou-emblem.png`
  - Mise a jour des references et des types dans `web/index.html` et `api.py`
- Out:
  - Toucher a `spikes/pwa-local-engine/`: bac a sable hors production.
  - Modifier les captures de `docs/assets/`.
  - Ajouter un fond, une plaque de couleur ou un cartouche derriere un asset transparent.

# Acceptance criteria
- AC1: Les trois PNG et l'ICO derivent des masters attendus.
- AC2: `web/index.html` et `api.py` ne referencent plus de SVG pour ces assets.
- AC3: Favicon et embleme s'affichent correctement sur le fond sombre.

# AC Traceability
- request-AC1 -> This backlog slice. Proof: AC1: Les trois PNG et l'ICO derivent des masters attendus.
- request-AC2 -> This backlog slice. Proof: AC2: `web/index.html` et `api.py` ne referencent plus de SVG pour ces assets.
- request-AC3 -> This backlog slice. Proof: AC3: Favicon et embleme s'affichent correctement sur le fond sombre.
- request-AC4 -> This backlog slice. Proof: AC3: Favicon et embleme s'affichent correctement sur le fond sombre.

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
