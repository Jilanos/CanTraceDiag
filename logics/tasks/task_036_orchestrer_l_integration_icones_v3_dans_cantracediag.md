## task_036_orchestrer_l_integration_icones_v3_dans_cantracediag - Orchestrer l'integration Icones V3 dans CanTraceDiag
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: Medium
> Theme: Implementation delivery
> Reminder: Update status/understanding/confidence/progress and linked request/backlog references when you edit this doc.
> Owner: Codex

# Context
- Orchestrate the scaffolded request chain and keep sibling implementation slices linked.

# Plan
- [x] 1. Inventorier favicon, manifest PWA, embleme top bar et lien parent existants.
- [x] 2. Copier les assets CanTraceDiag et Paul Mondou Icones V3 dans le repo.
- [x] 3. Mettre a jour les references, verifier cache PWA, accessibilite et responsive.
- [x] 4. Executer la validation locale PWA/build et preparer la preuve de livraison release.
- [x] ADR 009 checkpoint: update affected Logics docs during each meaningful wave and leave the repo commit-ready.
- [x] Keep commit creation under operator control; do not force one commit per micro-step.
- [x] GATE: do not close until lint, audit, and scaffold validation pass.

# Backlog
- `item_034_remplacer_favicon_et_embleme_cantracediag_par_icones_v3`
- `item_035_mettre_le_lien_parent_paul_mondou_aux_couleurs_icones_v3`

# Definition of Done (DoD)
- [x] Generated request, product, backlog, and task docs are present.
- [x] Context-pack handoff is available when requested.
- [x] Validation passes.
- [x] Meaningful waves followed ADR 009: affected docs updated and the repo left commit-ready without automatic commits.

# AC Traceability
- request-AC1, request-AC2, request-AC4 -> `item_034_remplacer_favicon_et_embleme_cantracediag_par_icones_v3`. Proof: `src/cantracediag/web/app-icon.svg` is overwritten from the CanTraceDiag Icones V3 icon, `src/cantracediag/web/app-emblem.svg` is a repository-local Icones V3 emblem, and the top-bar mark in `src/cantracediag/web/index.html` renders it via a version-stamped static asset.
- request-AC3, request-AC4 -> `item_035_mettre_le_lien_parent_paul_mondou_aux_couleurs_icones_v3`. Proof: the parent link keeps the `https://paulmondou.fr/` destination while rendering repository-local `src/cantracediag/web/paulmondou-emblem.png`, overwritten from Paul Mondou Icones V3 and covered by static asset versioning.

# Validation
- Local validation passed: `.venv/bin/ruff check .`, `CI=true .venv/bin/pytest` (155 passed), `node --experimental-strip-types --test spikes/pwa-local-engine/tests/*.test.ts` (20 passed), and `node spikes/pwa-local-engine/build-browser.mjs`.
- Logics validation passed: `logics-manager lint --require-status`, scoped `logics-manager flow validate`, and `logics-manager audit --legacy-cutoff-version 1.1.0 --group-by-doc` with only pre-existing Mermaid warnings on `prod_003` and `prod_004`.
- Remote validation passed: GitHub CI run `31023696323` succeeded on commit `1b54232cf26b1c60f33df8692b74bd32c45fa6e7`; release-by-tag run `31023993666` succeeded for `v1.0.6` including validate, publish, deploy, and release jobs; the public page shows `v1.0.6`, `app-emblem`, `app-icon`, and `paulmondou-emblem` references.
- CanTraceDiag v1.0.6 local checks, GitHub CI 31023696323, release deployment 31023993666, audit, and public page verification passed.
- Finish workflow executed on 2026-08-05.
- Linked backlog/request close verification passed.

# Report
- CanTraceDiag Icones V3 favicon, top-bar emblem, and Paul Mondou parent-link identity are integrated, versioned as `1.0.6`, tagged `v1.0.6`, and deployed.
- Finished on 2026-08-05.
- Linked backlog item(s): `item_034_remplacer_favicon_et_embleme_cantracediag_par_icones_v3`, `item_035_mettre_le_lien_parent_paul_mondou_aux_couleurs_icones_v3`
- Related request(s): `req_017_integrer_les_icones_icones_v3_et_le_lien_parent_paul_mondou_dans_cantracediag`

# AI Context
- Summary: Orchestrer l'integration Icones V3 dans CanTraceDiag
- Keywords: scaffolded-task, request-chain-scaffold, orchestration
- Use when: Coordinating implementation of a scaffolded request chain.
- Skip when: Working on one isolated sibling slice.

# Links
- Request: `req_017_integrer_les_icones_icones_v3_et_le_lien_parent_paul_mondou_dans_cantracediag`
- Product brief(s): `prod_005_identite_cantracediag_alignee_sur_icones_v3`
- Architecture decision(s): (none yet)
