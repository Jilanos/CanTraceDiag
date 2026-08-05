## item_034_remplacer_favicon_et_embleme_cantracediag_par_icones_v3 - Remplacer favicon et embleme CanTraceDiag par Icones V3
> From version: 1.0.0
> Schema version: 1.0
> Status: In progress
> Understanding: 90%
> Confidence: 85%
> Progress: 10%
> Complexity: Medium
> Theme: Branding
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- La PWA doit afficher les nouveaux assets CanTraceDiag sans reference runtime au dossier local Icones V3.

# Scope
- In:
  - Identifier favicon, manifest PWA, metadata et embleme dans la top bar.
  - Copier les SVG CanTraceDiag Icones V3 dans les assets du repo.
  - Mettre a jour les references light/dark et verifier le cache PWA si applicable.
- Out:
  - Changer le moteur de diagnostic ou les formats d'import.
  - Modifier la logique service worker hors invalidation des assets remplaces si necessaire.

# Acceptance criteria
- AC1: Le favicon et le manifest PWA resolvent l'icone CanTraceDiag Icones V3.
- AC2: L'embleme de top bar utilise l'asset CanTraceDiag Icones V3.
- AC3: La validation PWA ou build confirme la presence des assets references.

# AC Traceability
- request-AC1 -> This backlog slice. Proof: AC1: Le favicon et le manifest PWA resolvent l'icone CanTraceDiag Icones V3.
- request-AC2 -> This backlog slice. Proof: AC2: L'embleme de top bar utilise l'asset CanTraceDiag Icones V3.
- request-AC4 -> This backlog slice. Proof: AC3: La validation PWA ou build confirme la presence des assets references.

# Decision framing
- Product framing: Not needed
- Architecture framing: Not needed

# Links
- Product brief(s): `prod_005_identite_cantracediag_alignee_sur_icones_v3`
- Architecture decision(s): (none yet)
- Request: `req_017_integrer_les_icones_icones_v3_et_le_lien_parent_paul_mondou_dans_cantracediag`
- Primary task(s): `task_036_orchestrer_l_integration_icones_v3_dans_cantracediag`

# AI Context
- Summary: Remplacer favicon et embleme CanTraceDiag par Icones V3
- Keywords: scaffolded-backlog, remplacer favicon et embleme cantracediag par icones v3, implementation-ready
- Use when: Implementing the scaffolded slice for Remplacer favicon et embleme CanTraceDiag par Icones V3.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: High - les assets d'identite sont visibles dans la PWA et le navigateur
- Rationale: Set by scaffold input or defaulted for grooming.
