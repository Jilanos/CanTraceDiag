## task_039_remplacer_les_assets_cantracediag_par_les_masters_icones_v3_corriges - Remplacer les assets CanTraceDiag par les masters Icones V3 corriges
> From version: 1.0.0
> Schema version: 1.0
> Status: In progress
> Understanding: 90%
> Confidence: 85%
> Progress: 60%
> Complexity: Medium
> Theme: Implementation delivery
> Reminder: Update status/understanding/confidence/progress and linked request/backlog references when you edit this doc.
> Owner: Claude

# Context
- Orchestrate the scaffolded request chain and keep sibling implementation slices linked.

# Plan
- [ ] 1. Copier les masters vers `src/cantracediag/web/` au format PNG.
- [ ] 2. Regenerer `app-icon.ico` depuis le master icone.
- [ ] 3. Mettre a jour les references dans `web/index.html` et `api.py`.
- [ ] 4. Retirer les SVG orphelins puis controler le rendu.
- [ ] 5. Preparer la version `1.0.7` -> `1.0.8` dans `pyproject.toml` et `src/cantracediag/__init__.py`.
- [ ] 6. Committer `Prepare ... v1.0.8`, pousser sur `main` et attendre le CI vert sur ce commit.
- [ ] 7. Creer et pousser le tag annote `v1.0.8`, puis verifier les quatre jobs du workflow release.
- [ ] 8. Consigner SHA, tag et URL du run dans le closeout.
- [ ] ADR 009 checkpoint: update affected Logics docs during each meaningful wave and leave the repo commit-ready.
- [ ] Keep commit creation under operator control; do not force one commit per micro-step.
- [ ] GATE: do not close until lint, audit, and scaffold validation pass.

# Backlog
- `item_038_remplacer_les_assets_web_et_l_ico_cantracediag`
- `item_039_publier_la_version_1_0_8_apres_remplacement_des_assets`

# Definition of Done (DoD)
- [ ] Generated request, product, backlog, and task docs are present.
- [ ] Context-pack handoff is available when requested.
- [ ] Validation passes.
- [ ] Meaningful waves followed ADR 009: affected docs updated and the repo left commit-ready without automatic commits.

# AC Traceability
- request-AC1, request-AC2, request-AC3, request-AC4 -> `item_038_remplacer_les_assets_web_et_l_ico_cantracediag`. Proof deferred to slice closeout.
- request-AC5 -> `item_039_publier_la_version_1_0_8_apres_remplacement_des_assets`. Proof deferred to slice closeout.

# Validation
- (no validation recorded yet)

# Report
- Not started.

# AI Context
- Summary: Remplacer les assets CanTraceDiag par les masters Icones V3 corriges
- Keywords: scaffolded-task, request-chain-scaffold, orchestration
- Use when: Coordinating implementation of a scaffolded request chain.
- Skip when: Working on one isolated sibling slice.

# Links
- Request: `req_020_remplacer_les_assets_cantracediag_par_les_masters_icones_v3_corriges`
- Product brief(s): `prod_007_identite_cantracediag_alignee_sur_icones_v3_corrige`
- Architecture decision(s): (none yet)
