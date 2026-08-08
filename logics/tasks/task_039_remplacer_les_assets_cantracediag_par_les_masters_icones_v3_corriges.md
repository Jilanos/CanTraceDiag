## task_039_remplacer_les_assets_cantracediag_par_les_masters_icones_v3_corriges - Remplacer les assets CanTraceDiag par les masters Icones V3 corriges
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 95%
> Confidence: 92%
> Progress: 100%
> Complexity: Medium
> Theme: Implementation delivery
> Reminder: Update status/understanding/confidence/progress and linked request/backlog references when you edit this doc.
> Owner: Claude

# Context
- Orchestrate the scaffolded request chain and keep sibling implementation slices linked.

# Plan
- [x] 1. Copier les masters `Icones V3/a black/SVG upgraded` vers `src/cantracediag/web/` au format SVG (app-icon, app-emblem, paulmondou-emblem).
- [x] 2. Regenerer `app-icon.ico` (16/32/48/64/128/256) depuis le master SVG.
- [x] 3. Mettre a jour les references dans `web/index.html`, le build PWA, `sw.js`, le manifest et `pyproject.toml`.
- [x] 4. Retirer les PNG orphelins puis controler le rendu.
- [x] 5. Preparer la version `1.0.8` -> `1.0.9` dans `pyproject.toml` et `src/cantracediag/__init__.py`.
- [x] 6. Committer, pousser sur `main` et attendre le CI vert sur ce commit.
- [x] 7. Creer et pousser le tag annote `v1.0.9`, puis verifier les quatre jobs du workflow release.
- [x] 8. Consigner SHA, tag et URL du run dans le closeout.
- [x] ADR 009 checkpoint: update affected Logics docs during each meaningful wave and leave the repo commit-ready.
- [x] Keep commit creation under operator control; do not force one commit per micro-step.
- [x] GATE: do not close until lint, audit, and scaffold validation pass.

# Backlog
- `item_038_remplacer_les_assets_web_et_l_ico_cantracediag`
- `item_039_publier_la_version_1_0_8_apres_remplacement_des_assets`

# Definition of Done (DoD)
- [x] Generated request, product, backlog, and task docs are present.
- [x] Context-pack handoff is available when requested.
- [x] Validation passes.
- [x] Meaningful waves followed ADR 009: affected docs updated and the repo left commit-ready without automatic commits.

# AC Traceability
- request-AC1 -> `item_038_remplacer_les_assets_web_et_l_ico_cantracediag`. Proof: `app-icon.svg`, `app-emblem.svg` et `paulmondou-emblem.svg` sont les masters `Icones V3/a black/SVG upgraded` copies sans modification (5593 et 47973 octets, identiques a la source); `app-icon.ico` (16/32/48/64/128/256) et les icones PWA 192/512 sont rasterises depuis ce meme master.
- request-AC2 -> `item_038_remplacer_les_assets_web_et_l_ico_cantracediag`. Proof: `pytest` (134 passed) couvre les references versionnees du shell FastAPI; `node spikes/pwa-local-engine/build-browser.mjs` rebatit le site sans ENOENT; en production `assets/*.svg` repondent 200 en `image/svg+xml` et `assets/app-icon-{192,512}.png` en `image/png`.
- request-AC3 -> `item_038_remplacer_les_assets_web_et_l_ico_cantracediag`. Proof: capture de https://cantracediag.paulmondou.fr/ en 1280x220 apres deploiement: embleme d'en-tete et embleme du lien parent lisibles sur le fond sombre, version `v1.0.9` affichee.
- request-AC4 -> `item_038_remplacer_les_assets_web_et_l_ico_cantracediag`. Proof: les SVG servis sont les masters transparents inchanges; les rasters sont produits avec `--default-background-color=00000000`, sans plaque ni cartouche ajoute.
- request-AC5 -> `item_039_publier_la_version_1_0_8_apres_remplacement_des_assets`. Proof: commit `ac9a58c` (CI verte, run 31272827151), tag annote `v1.0.9` sur ce SHA, workflow release 31272908558 vert sur validate, publish, deploy et release.

# Validation
- `pytest` : 134 passed, 21 skipped.
- `ruff check .` : All checks passed.
- `node --experimental-strip-types --test spikes/pwa-local-engine/tests/*.test.ts` : 20 passed.
- `node spikes/pwa-local-engine/build-browser.mjs` : site rebati, `site/assets/` ne contient plus de PNG d'identite orphelin.
- Finish workflow executed on 2026-08-08.
- Linked backlog/request close verification passed.

# Report
- Les livraisons v1.0.7 et v1.0.8 utilisaient les mauvais masters (PNG du dossier `Icones V3/cantracediag`).
  Les masters corrects sont les SVG de `Icones V3/a black/SVG upgraded`.
- Finished on 2026-08-08.
- Linked backlog item(s): `item_038_remplacer_les_assets_web_et_l_ico_cantracediag`, `item_039_publier_la_version_1_0_8_apres_remplacement_des_assets`
- Related request(s): `req_020_remplacer_les_assets_cantracediag_par_les_masters_icones_v3_corriges`
- `app-icon.svg`, `app-emblem.svg` et `paulmondou-emblem.svg` remplacent les PNG dans `src/cantracediag/web/`.
- `app-icon.ico` et les icones PWA 192/512 sont rasterises depuis le nouveau master SVG.
- Le manifest reprend l'entree SVG `sizes: any` et garde les deux PNG maskables exiges par le smoke test.

# Closeout
- Commit: `ac9a58c381b65e4f538126e93faca9b98eaea00d` sur `main`.
- CI sur ce SHA: succes - https://github.com/Jilanos/CanTraceDiag/actions/runs/31272827151
- Tag annote: `v1.0.9` -> `ac9a58c`.
- Release: succes sur validate, publish, deploy et release - https://github.com/Jilanos/CanTraceDiag/actions/runs/31272908558
- Verification en production sur https://cantracediag.paulmondou.fr/ : version `v1.0.9` affichee;
  `assets/app-icon.svg`, `assets/app-emblem.svg` et `assets/paulmondou-emblem.svg` servis en `image/svg+xml`;
  `assets/app-icon-192.png` et `assets/app-icon-512.png` servis en `image/png`.
  Les anciens chemins PNG ne renvoient plus que le fallback SPA `text/html`.

# AI Context
- Summary: Remplacer les assets CanTraceDiag par les masters Icones V3 corriges
- Keywords: scaffolded-task, request-chain-scaffold, orchestration
- Use when: Coordinating implementation of a scaffolded request chain.
- Skip when: Working on one isolated sibling slice.

# Links
- Request: `req_020_remplacer_les_assets_cantracediag_par_les_masters_icones_v3_corriges`
- Product brief(s): `prod_007_identite_cantracediag_alignee_sur_icones_v3_corrige`
- Architecture decision(s): (none yet)
