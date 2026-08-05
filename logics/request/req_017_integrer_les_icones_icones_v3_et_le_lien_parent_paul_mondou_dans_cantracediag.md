## req_017_integrer_les_icones_icones_v3_et_le_lien_parent_paul_mondou_dans_cantracediag - Integrer les icones Icones V3 et le lien parent Paul Mondou dans CanTraceDiag
> From version: 1.0.0
> Schema version: 1.0
> Status: Draft
> Understanding: 90%
> Confidence: 85%
> Complexity: Medium
> Theme: Branding
> Reminder: Update status/understanding/confidence and linked backlog/task references when you edit this doc.

# Needs
- Utiliser les assets CanTraceDiag du corpus Icones V3 pour l'icone d'onglet et l'embleme.
- Utiliser les assets Paul Mondou du corpus Icones V3 pour le lien parent.

# Context
- Le dossier source est le corpus local Icones V3 fourni par l'operateur; les chemins references ici sont internes a ce corpus pour respecter les regles Logics.
- Assets attendus: cantracediag/cantracediag-icon-light.svg, cantracediag/cantracediag-icon-dark.svg, cantracediag/cantracediag-emblem-light.svg, cantracediag/cantracediag-emblem-dark.svg, puis les assets paulmondou pour le lien parent.
- CanTraceDiag a deja une demande autour du lien parent et de la version dans la top bar; ce corpus precise le remplacement Icones V3.

# Acceptance criteria
- AC1: L'icone d'onglet CanTraceDiag utilise l'asset CanTraceDiag Icones V3.
- AC2: L'embleme CanTraceDiag visible dans l'interface utilise l'asset CanTraceDiag Icones V3.
- AC3: Le lien vers Paul Mondou utilise l'identite Paul Mondou Icones V3 et conserve sa destination parent.
- AC4: Les assets necessaires sont integres au repo CanTraceDiag et ne dependent pas du dossier local au runtime.

# Definition of Ready (DoR)
- [x] Problem statement is explicit and user impact is clear.
- [x] Scope boundaries (in/out) are explicit.
- [x] Acceptance criteria are testable.
- [x] Dependencies and known risks are listed.

# Companion docs
- Product brief(s): `prod_005_identite_cantracediag_alignee_sur_icones_v3`
- Architecture decision(s): (none yet)

# References
- Corpus externe Icones V3/cantracediag/
- Corpus externe Icones V3/paulmondou/
- logics/request/req_016_ajouter_le_lien_parent_et_la_version_dans_la_top_barre.md
- logics/backlog/item_033_ajouter_le_lien_parent_et_la_version_dans_la_top_barre.md

# AI Context
- Summary: Integrer les icones Icones V3 et le lien parent Paul Mondou dans CanTraceDiag
- Keywords: request-chain-scaffold, integrer les icones icones v3 et le lien parent paul mondou dans cantracediag, development-ready
- Use when: You need to implement or review the scaffolded workflow for Integrer les icones Icones V3 et le lien parent Paul Mondou dans CanTraceDiag.
- Skip when: The change is unrelated to this scaffolded request chain.

# Backlog
- `item_034_remplacer_favicon_et_embleme_cantracediag_par_icones_v3`
- `item_035_mettre_le_lien_parent_paul_mondou_aux_couleurs_icones_v3`
