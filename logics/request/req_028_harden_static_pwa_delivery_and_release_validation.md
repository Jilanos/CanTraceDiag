## req_028_harden_static_pwa_delivery_and_release_validation - Harden static PWA delivery and release validation
> From version: 1.0.0
> Schema version: 1.0
> Status: Draft
> Understanding: 90%
> Confidence: 85%
> Complexity: Medium
> Theme: Static PWA delivery integrity
> Reminder: Update status/understanding/confidence and linked backlog/task references when you edit this doc.
> Indicators reviewed: 2026-08-23 09:47:01

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
