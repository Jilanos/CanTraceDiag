## task_035_ajouter_le_lien_parent_et_la_version_dans_la_top_barre - Ajouter le lien parent et la version dans la top barre
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
- `item_033_ajouter_le_lien_parent_et_la_version_dans_la_top_barre`

# Acceptance criteria
- AC1: La top barre contient un lien accessible vers `https://paulmondou.fr/`
  dont le contenu visuel utilise l'embleme Paul Mondou fourni.
- AC2: L'embleme est copie dans les assets applicatifs versionnes et reference
  par l'interface sans dependance au chemin local externe de l'operateur.
- AC3: La top barre affiche le numero de version de CanTraceDiag et cette valeur
  provient d'une surface canonique synchronisee avec la version release.
- AC4: Les dimensions et etats responsives de la top barre restent stables sur
  desktop et mobile.
- AC5: La validation locale couvre le rendu web/PWA pertinent et la coherence
  de version.
- AC6: La livraison applique la sequence classique du depot : validation locale,
  commit d'implementation, preparation SemVer, commit de version, push, attente
  CI, tag annote `vX.Y.Z`, verification release, ou consigne un blocage externe.

# Plan
- [x] Identifier la top barre, la surface de version canonique et le chemin de
  build/deploiement du projet.
- [x] Copier l'embleme Paul Mondou adapte dans les assets versionnes.
- [x] Ajouter le lien parent et la version dans la top barre avec rendu stable.
- [x] Valider localement le rendu et la coherence de version.
- [x] Executer la politique classique de deploiement ou documenter le blocage
  externe exact.
- [x] Run `python3 -m logics_manager flow finish task task_035_ajouter_le_lien_parent_et_la_version_dans_la_top_barre.md` after implementation.

# Validation
- Planned:
  - `python -m pytest`
  - web/PWA smoke or build command identified from the repository
  - `logics-manager lint --require-status`
  - `logics-manager audit --legacy-cutoff-version 1.1.0 --group-by-doc`
- PASSED 2026-08-04: `.venv/bin/python -m pytest` passed 155 tests.
- PASSED 2026-08-04: `.venv/bin/ruff check .` returned `All checks passed!`.
- PASSED 2026-08-04: `node spikes/pwa-local-engine/build-browser.mjs`
- Local 2026-08-04: .venv/bin/python -m pytest passed 155 tests; .venv/bin/ruff check . passed; node spikes/pwa-local-engine/build-browser.mjs passed; logics-manager lint --require-status passed; logics-manager audit --legacy-cutoff-version 1.1.0 --group-by-doc passed with 0 blocking issues and 2 pre-existing Mermaid warnings. Implementation commit b9b10a1. Version commit 8b19002. main CI run 30912217630 passed on 8b19002. Annotated tag v1.0.5 pushed. Release by tag run 30912391674 passed including validate, publish, deploy and GitHub release. Tag CI run 30912392010 passed.
- Finish workflow executed on 2026-08-04.
- Linked backlog/request close verification passed.
  built `spikes/pwa-local-engine/site` and copied the Paul Mondou emblem asset.
- PASSED 2026-08-04: `logics-manager lint --require-status` returned OK.
- PASSED 2026-08-04: `logics-manager audit --legacy-cutoff-version 1.1.0
  --group-by-doc` returned 0 blocking issues; the 2 warnings are pre-existing
  missing Mermaid diagrams in product companion docs.
- PASSED 2026-08-04: GitHub Actions main CI run `30912217630` passed on
  version commit `8b19002`.
- PASSED 2026-08-04: annotated tag `v1.0.5` was pushed and Release by tag run
  `30912391674` passed validate, publish, deploy and GitHub release jobs.
- PASSED 2026-08-04: tag CI run `30912392010` passed.

# Report
- Started from operator request on 2026-08-04.
- Implemented in commit `b9b10a1`.
- Version prepared in commit `8b19002`.
- Released as `v1.0.5`.
- Finished on 2026-08-04.
- Linked backlog item(s): `item_033_ajouter_le_lien_parent_et_la_version_dans_la_top_barre`
- Related request(s): `req_016_ajouter_le_lien_parent_et_la_version_dans_la_top_barre`

# AI Context
- Summary: Implement ajouter le lien parent et la version dans la top barre.
- Keywords: task, implementation, backlog, runtime, python
- Use when: You need a bounded implementation task for a backlog item.
- Skip when: The work is still at the request or backlog shaping stage.

# Links
- Request: `req_016_ajouter_le_lien_parent_et_la_version_dans_la_top_barre`
- Product brief(s): (none yet)
- Architecture decision(s): (none yet)

# AC Traceability
- request-AC1 -> This task. Proof: `src/cantracediag/web/index.html`
  contains the `https://paulmondou.fr/` parent link and emblem image.
- request-AC2 -> This task. Proof: `src/cantracediag/web/paulmondou-emblem.png`
  is a versioned app asset, packaged via `pyproject.toml`, copied by the PWA
  build and tested in `tests/test_api.py`.
- request-AC3 -> This task. Proof: FastAPI replaces `__CTD_APP_VERSION__` with
  `cantracediag.__version__`; the PWA build reads the version from
  `pyproject.toml`; `tests/test_imports.py` verifies both surfaces match.
- request-AC4 -> This task. Proof: changes are limited to top-bar HTML/CSS,
  one emblem asset, version propagation, tests and Logics delivery docs.
- request-AC5 -> This task. Proof: local validation, main CI `30912217630`, tag
  `v1.0.5`, release workflow `30912391674` and tag CI `30912392010` all passed.
