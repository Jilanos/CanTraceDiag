## req_020_remplacer_les_assets_cantracediag_par_les_masters_icones_v3_corriges - Remplacer les assets CanTraceDiag par les masters Icones V3 corriges
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 95%
> Confidence: 92%
> Complexity: High
> Theme: Brand asset integration
> Reminder: Update status/understanding/confidence and linked backlog/task references when you edit this doc.
> Indicators reviewed: 2026-08-06

# Needs
- Remplacer l'icone, l'embleme et l'ICO par les masters corriges, variantes `-dark`.

# Context
- Correction operateur du 2026-08-08: les masters approuves sont les SVG de
  `WORK/perso/Icones V3/a black/SVG upgraded`, pas les PNG de `Icones V3/<marque>/`.
  Les livraisons v1.0.7 et v1.0.8 reposaient sur le mauvais lot.
- Les masters sont des SVG en viewBox 1024x1024, a fond transparent.
- Le suffixe de variante designe le contour: `-dark` porte un lisere pale et se pose sur fond sombre, `-light` porte un contour navy et se pose sur fond clair.
- Le lot Icones V3 precedemment integre reposait sur de mauvaises images: ce corpus corrige la source, pas la demarche.
- Certaines marques n'ont qu'un ou deux masters (Gnosis, Paul Mondou, Kapsule, F1 Datas). Consigne operateur: reutiliser ce master unique pour l'embleme comme pour l'icone.
- Les quatorze masters sont a fond transparent: coins a alpha=0 et 28% a 87% de pixels transparents selon l'asset. Consigne operateur: ne rien ajouter derriere, ni en favicon ni en embleme.
- Le SVG etant vectoriel, il est servi tel quel pour le favicon, l'embleme et l'icone de manifest. Seules les surfaces qui exigent du raster restent rasterisees: ICO multi-tailles 16/32/48/64/128/256 et icones PWA maskables 192 et 512 px.
- L'interface est sombre (`--bg-deep: #05080c`) et sans bascule de theme: les variantes `-dark` sont celles qui conviennent.
- Le retour au SVG restaure `app-icon.svg` et `app-emblem.svg` dans `web/index.html`, le manifest et le service worker.
- `app-icon.ico` est servi par `api.py` et doit etre regenere depuis le master icone.

# Acceptance criteria
- AC1: Chaque fichier livre est le master SVG `Icones V3/a black/SVG upgraded` correspondant, ou un derive rasterise fidele de ce master a la taille d'usage declaree, sans perte de transparence.
- AC2: Aucune reference d'asset n'est cassee apres remplacement, extensions et types MIME inclus.
- AC3: Le rendu est verifie visuellement sur le theme reellement servi par l'application.
- AC4: La transparence des masters est preservee: aucun fond, plaque ou cartouche n'est ajoute derriere l'asset, favicon et embleme compris.
- AC5: La livraison se termine par un commit de version X.Y.Z+1, un push, puis un tag annote vX.Y.Z+1 dont le workflow release est vert.

# Definition of Ready (DoR)
- [x] Problem statement is explicit and user impact is clear.
- [x] Scope boundaries (in/out) are explicit.
- [x] Acceptance criteria are testable.
- [x] Dependencies and known risks are listed.

# Companion docs
- Product brief(s): `prod_007_identite_cantracediag_alignee_sur_icones_v3_corrige`
- Architecture decision(s): (none yet)

# References
- WORK/perso/Icones V3/

# AI Context
- Summary: Remplacer les assets CanTraceDiag par les masters Icones V3 corriges
- Keywords: request-chain-scaffold, remplacer les assets cantracediag par les masters icones v3 corriges, development-ready
- Use when: You need to implement or review the scaffolded workflow for Remplacer les assets CanTraceDiag par les masters Icones V3 corriges.
- Skip when: The change is unrelated to this scaffolded request chain.

# Backlog
- `item_038_remplacer_les_assets_web_et_l_ico_cantracediag`
- `item_039_publier_la_version_1_0_8_apres_remplacement_des_assets`
