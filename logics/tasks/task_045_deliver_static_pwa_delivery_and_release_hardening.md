## task_045_deliver_static_pwa_delivery_and_release_hardening - Deliver static PWA delivery and release hardening
> From version: 1.0.0
> Schema version: 1.0
> Status: In progress
> Understanding: 90%
> Confidence: 85%
> Progress: 90%
> Complexity: Medium
> Theme: Implementation delivery
> Reminder: Update status/understanding/confidence/progress and linked request/backlog references when you edit this doc.
> Indicators reviewed: 2026-08-23 10:07:15
> Owner: codex

# AI Context
- Summary: Orchestrate delivery of the audit response across PWA bundle integrity, generated-site smoke automation, Docker context reduction, and residual governance hardening.
- Keywords: deliver, static, pwa, delivery, release, hardening
- Use when: Starting or coordinating implementation of the full `req_028` audit-response chain.
- Skip when: Grooming unrelated requests or implementing a single sibling backlog item under a separate task.

# Context
- Orchestrate the scaffolded request chain and keep sibling implementation slices linked.

# Plan
- [ ] 1. Start by reproducing the audited fullscreen omission against the generated PWA bundle and adding a failing module-parity regression test.
- [ ] 2. Fix static PWA module discovery or validation so the source HTML shell and generated bundle cannot diverge silently, then verify fullscreen behavior in the built site.
- [ ] 3. Make the generated-site browser smoke deterministic and wire it into pull-request CI and release validation with a stable fullscreen-control assertion.
- [ ] 4. Reduce Docker context size without changing the served PWA artifact, then record the measured effect.
- [ ] 5. Work through the residual audit items as a disposition table, using Logics lifecycle commands for stale records and scoped follow-up docs for larger architecture or supply-chain work.
- [ ] 6. Run the standard local validation suite, Logics lint, Logics audit, and the repository release workflow sequence required for functional changes; record all evidence before closeout.
- [ ] ADR 009 checkpoint: update affected Logics docs during each meaningful wave and leave the repo commit-ready.
- [ ] Keep commit creation under operator control; do not force one commit per micro-step.
- [ ] GATE: do not close until lint, audit, and scaffold validation pass.

# Backlog
- `item_049_prevent_static_pwa_module_omissions_and_restore_fullscreen_delivery`
- `item_050_run_generated_site_browser_smoke_in_ci_and_release_validation`
- `item_051_shrink_docker_build_context_for_the_static_pwa_image`
- `item_052_resolve_residual_audit_governance_and_release_hardening_debt`

# Definition of Done (DoD)
- [ ] Generated request, product, backlog, and task docs are present.
- [ ] Context-pack handoff is available when requested.
- [ ] Validation passes.
- [ ] Meaningful waves followed ADR 009: affected docs updated and the repo left commit-ready without automatic commits.

# AC Traceability
- request-AC1 -> `item_049_prevent_static_pwa_module_omissions_and_restore_fullscreen_delivery`. Proof: module list derived from the HTML shell with a build-time divergence guard and a regression test that failed at cab567b and passes at e91cb8d.
- request-AC2 -> `item_049_prevent_static_pwa_module_omissions_and_restore_fullscreen_delivery`. Proof: module list derived from the HTML shell with a build-time divergence guard and a regression test that failed at cab567b and passes at e91cb8d.
- request-AC6 -> `item_049_prevent_static_pwa_module_omissions_and_restore_fullscreen_delivery`. Proof: module list derived from the HTML shell with a build-time divergence guard and a regression test that failed at cab567b and passes at e91cb8d.
- request-AC2 -> `item_050_run_generated_site_browser_smoke_in_ci_and_release_validation`. Proof: the generated-site browser smoke runs in the pull-request PWA job and the release validate job, and covers the fullscreen control (573f9f4).
- request-AC3 -> `item_050_run_generated_site_browser_smoke_in_ci_and_release_validation`. Proof: the generated-site browser smoke runs in the pull-request PWA job and the release validate job, and covers the fullscreen control (573f9f4).
- request-AC6 -> `item_050_run_generated_site_browser_smoke_in_ci_and_release_validation`. Proof: the generated-site browser smoke runs in the pull-request PWA job and the release validate job, and covers the fullscreen control (573f9f4).
- request-AC4 -> `item_051_shrink_docker_build_context_for_the_static_pwa_image`. Proof: build context 395.9 MB -> 951.3 kB with a byte-identical served artifact (ffc4b15).
- request-AC6 -> `item_051_shrink_docker_build_context_for_the_static_pwa_image`. Proof: build context 395.9 MB -> 951.3 kB with a byte-identical served artifact (ffc4b15).
- request-AC5 -> `item_052_resolve_residual_audit_governance_and_release_hardening_debt`. Proof: disposition table in this task's Report, with req_029 and req_030 opened for the split items (b04e7ec, 4415c0c).
- request-AC6 -> `item_052_resolve_residual_audit_governance_and_release_hardening_debt`. Proof: disposition table in this task's Report, with req_029 and req_030 opened for the split items (b04e7ec, 4415c0c).

# Validation
- (no validation recorded yet)

# Report
- Wave 1 (`item_049`) - bundle parity. `spikes/pwa-local-engine/product-modules.mjs` now derives the ordered product module list from `src/cantracediag/web/index.html`; the build fails when the shell and `src/cantracediag/web/js/` diverge in either direction, and stamps the bundled set into the artifact as a `// ctd:modules ...` marker. `spikes/pwa-local-engine/tests/product-bundle.test.ts` reproduced the audited omission before the fix (commit cab567b) and passes after it (commit e91cb8d). The delivered bundle now contains `fullscreen.js`.
- Wave 2 (`item_050`) - generated-site smoke in CI and release. The smoke defaults to the generated site, resolves Chromium through `CHROME_PATH`, the Playwright cache, then a distro browser instead of one developer's absolute path, and asserts the fullscreen contract: after a user-gesture click the control is either in fullscreen or shows a refusal note, with `aria-pressed` mirroring the native state. Verified negatively - removing only the click listener from the delivered bundle makes the smoke fail. Wired into the pull-request PWA job and the release `validate` job against a pinned Playwright Chromium (commit 573f9f4).
- Wave 3 (`item_051`) - Docker context. `.dockerignore` became an explicit exclusion list. Measured with the legacy builder on this machine: 395.9 MB before, 951.3 kB after (-99.8%). The served artifact is unchanged - `sha256` over `/usr/share/nginx/html` is identical between the before and after images (`7e3b4b75...8667`), and the container still answers 200 on `/` and serves `browser/product-app.mjs` as `application/javascript` (commit ffc4b15).
- Wave 4 (`item_052`) - residual audit debt, disposition table below (commits b04e7ec, 4415c0c).

## Residual audit disposition (`item_052`)
| Audit item | Disposition | Evidence |
| --- | --- | --- |
| C3 - production code under `spikes/`, fragile text-marker assembly | Split into new work | `req_029_promote_the_pwa_out_of_spikes_and_replace_text_marker_bundle_assembly`. This slice removed the duplicated module list but deliberately left `replaceBlock` and the directory move out of scope. |
| C4 - four Logics documents frozen for 31 days | Fixed | `req_007`/`item_017`/`task_017` withdrawn as Obsolete, superseded by `req_011`; their DoD records closure by withdrawal rather than delivery. `task_021`/`item_021` regrounded from 45% to 60%, matching the six of ten `req_011` acceptance criteria that carry evidence (AC1-AC5, AC8). `logics-manager health` now reports one stale document instead of four, and it is the live migration chain. |
| C5 - mutable image tags and inconsistent action pinning | Partly fixed, remainder split | `release.yml` now pins the checkout and setup actions to the same exact versions `ci.yml` uses. Digest pinning of base images and SHA pinning of third-party actions moved to `req_030_pin_supply_chain_images_and_actions_immutably`: pinning the publishing path by hand can only fail at release time, so it needs its own verified pass. |
| C6 - 383 MB of caches in the Docker context | Fixed | Wave 3 above. |
| C7 - Starlette test-client deprecation | Fixed | The `dev` extra installs `httpx2`; the suite went from 166 passed with 1 warning to 166 passed with none (commit b04e7ec). |
| C8 - `release.yml` validates less than `ci.yml` | Fixed | The release `validate` job gained the site file checks and the generated-site browser smoke; a new `validate-python` job runs Ruff and the Python suite, and `publish` now waits on both. The container MIME check stays out of the release gate because `publish` builds and pushes that exact image immediately afterwards, and the pull-request job already covers it. |

# Links
- Request: `req_028_harden_static_pwa_delivery_and_release_validation`
- Product brief(s): `prod_013_reliable_static_pwa_delivery`
- Architecture decision(s): (none yet)
