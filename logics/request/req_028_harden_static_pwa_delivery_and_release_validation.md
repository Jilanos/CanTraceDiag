## req_028_harden_static_pwa_delivery_and_release_validation - Harden static PWA delivery and release validation
> From version: 1.0.0
> Schema version: 1.0
> Status: Draft
> Understanding: 90%
> Confidence: 85%
> Complexity: Medium
> Theme: Static PWA delivery integrity
> Reminder: Update status/understanding/confidence and linked backlog/task references when you edit this doc.
> Indicators reviewed: 2026-08-23 10:07:15

# AI Context
- Summary: Turn the 2026-08-23 PWA delivery audit into scoped remediation work for bundle completeness, generated-site automation, Docker context size, and release hardening.
- Keywords: harden, static, pwa, delivery, release, validation
- Use when: Planning or implementing the audit response for static PWA build integrity and release validation.
- Skip when: Working on unrelated parser, DBC, chart, or diagnostic-report feature work.

# Needs
- Make the generated static PWA include every product web module required by the HTML shell, including the fullscreen controller.
- Exercise the generated browser application in automated pull-request and release validation so delivered-site regressions are caught before publication.
- Reduce delivery and governance drift found by the 2026-08-23 audit without expanding into unrelated product redesign.

# Context
- The source audit is `docs/audit-2026-08-23.md`, captured from revision `f9d4365` and summarized in `req_027_review_findings_pwa_delivery_integrity_and_release_hardening`.
- The immediate P0 defect is that `buildProductAppSource()` in `spikes/pwa-local-engine/build-browser.mjs` hard-codes a product module list that omits `fullscreen.js`, while `src/cantracediag/web/index.html` exposes `#fullscreenBtn` and `#fullscreenNote` and loads the missing module in the source shell.
- The generated PWA bundle contained no `fullscreen` reference during the audit, leaving the visible fullscreen button inert without a console error.
- The CI PWA job runs Node tests, the static build, static HTTP checks, and Docker MIME checks, but it does not invoke `spikes/pwa-local-engine/browser-smoke.mjs`; release validation is weaker than CI and likewise does not exercise the delivered browser surface.
- The Docker build context measured about 933 MB, with `.pydeps` contributing about 383 MB; `.dockerignore` also leaves tests, docs, Logics records, `.github`, `tmp`, and the historical `spikes/pwa-500mb` material in the broad `COPY . .` context.
- The audit also identified structural follow-up work: fragile text-marker source rewriting, production code still living under `spikes/`, stale Logics records, inconsistent or mutable supply-chain pins, and a Starlette test-client deprecation warning.
- The corpus is intended to make the audit actionable. Implementation must follow the repository release policy for functional changes: local validation, implementation commit, version-preparation commit, push, CI on the exact SHA, annotated tag, release verification, and closeout evidence.

# Acceptance criteria
- AC1: The generated static PWA includes every product web module required by the HTML shell, and a regression test fails if the source shell and build module set diverge.
- AC2: The delivered fullscreen control is exercised against the generated site and has observable behavior or explicit unsupported-browser feedback.
- AC3: Pull-request CI and release validation run a generated-site browser smoke that covers service worker/app-shell behavior, workspace persistence, and the fullscreen control.
- AC4: The Docker context excludes local dependency caches and non-production inputs without removing files required to build and serve the static PWA.
- AC5: Structural follow-ups for the fragile PWA assembly, production location under `spikes/`, stale workflow records, supply-chain pinning, and the Starlette deprecation are explicitly resolved, deferred with rationale, or split into follow-on work.
- AC6: Before closeout, Ruff, Python tests, Node PWA tests, PWA build, browser smoke, Logics lint, Logics audit, and the required release evidence are recorded.

# AC Traceability
- request-AC1 -> This task. Proof: the build derives its ordered module list from `src/cantracediag/web/index.html` via `spikes/pwa-local-engine/product-modules.mjs` and fails on divergence in either direction; `spikes/pwa-local-engine/tests/product-bundle.test.ts` failed on the audited omission at cab567b and passes at e91cb8d.
- request-AC2 -> This task. Proof: the delivered bundle contains `fullscreen.js`, and the generated-site browser smoke clicks `#fullscreenBtn` with a user gesture and requires either `document.fullscreenElement` or a visible refusal note, with `aria-pressed` mirroring the native state; on 2026-08-23 the delivered site entered and left fullscreen. Removing only the click listener from the built bundle makes the smoke fail.
- request-AC3 -> This task. Proof: `.github/workflows/ci.yml` and the `validate` job of `.github/workflows/release.yml` both install a pinned Playwright Chromium and run `node spikes/pwa-local-engine/browser-smoke.mjs` against the generated site, which asserts app shell, service worker, workspace persistence, CSV export, zero `/api` calls, and the fullscreen control (573f9f4).
- request-AC4 -> This task. Proof: `.dockerignore` became an explicit exclusion list; the measured build context fell from 395.9 MB to 951.3 kB while `sha256` over `/usr/share/nginx/html` stayed identical between the before and after images, and the container still served `browser/product-app.mjs` as `application/javascript` (ffc4b15).
- request-AC5 -> This task. Proof: the residual disposition table in `task_045_deliver_static_pwa_delivery_and_release_hardening` gives C3, C4, C5, C7 and C8 a concrete outcome - C4/C7/C8 fixed here, C3 split into `req_029`, C5 partly fixed and the remainder split into `req_030` (b04e7ec, 4415c0c).
- request-AC6 -> This task. Proof: recorded in the task's Validation section - Ruff, 166 pytest tests, 32 Node PWA tests, the static build, the generated-site browser smoke, `logics-manager lint --require-status`, `logics-manager audit`, and the release evidence for the version published from this chain.

# Definition of Ready (DoR)
- [x] Problem statement is explicit and user impact is clear.
- [x] Scope boundaries (in/out) are explicit.
- [x] Acceptance criteria are testable.
- [x] Dependencies and known risks are listed.

# Companion docs
- Product brief(s): `prod_013_reliable_static_pwa_delivery`
- Architecture decision(s): (none yet)

# References
- logics/request/req_027_review_findings_pwa_delivery_integrity_and_release_hardening.md
- docs/audit-2026-08-23.md
- spikes/pwa-local-engine/build-browser.mjs
- spikes/pwa-local-engine/browser-smoke.mjs
- src/cantracediag/web/index.html
- src/cantracediag/web/js/fullscreen.js
- .github/workflows/ci.yml
- .github/workflows/release.yml
- .dockerignore
- Dockerfile
- tests/conftest.py

# Backlog
- `item_049_prevent_static_pwa_module_omissions_and_restore_fullscreen_delivery`
- `item_050_run_generated_site_browser_smoke_in_ci_and_release_validation`
- `item_051_shrink_docker_build_context_for_the_static_pwa_image`
- `item_052_resolve_residual_audit_governance_and_release_hardening_debt`
