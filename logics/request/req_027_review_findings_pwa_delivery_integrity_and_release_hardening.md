## req_027_review_findings_pwa_delivery_integrity_and_release_hardening - Review findings: PWA delivery integrity and release hardening
> From version: 1.0.0
> Schema version: 1.0
> Status: Draft
> Understanding: 90%
> Confidence: 85%
> Complexity: Medium
> Theme: General
> Reminder: Update status/understanding/confidence and linked backlog/task references when you edit this doc.

# AI Context
- Summary: Capture verified audit findings about static PWA assembly, delivered-browser coverage, delivery efficiency, and release assurance.
- Keywords: review, findings, pwa, delivery, integrity, release, hardening
- Use when: Triage the 2026-08-23 audit into independently scoped remediation work.
- Skip when: Implementing a remediation that has already been scoped into a backlog item.

# Needs
- Preserve the audit candidates that affect the delivered static PWA and its release path. The immediate user-facing defect is that the built PWA omits the fullscreen controller although the control is present in its HTML shell and documented as available.
- Ensure any later remediation prevents source modules from silently disappearing during static-PWA assembly and exercises real built-site behavior in automation.
- Reduce delivery risk and maintenance drift identified in the audit: an oversized Docker context, an obsolete spike location/fragile text rewriting, stale workflow records, inconsistent dependency pinning, and a pending test-client deprecation.

# Context
- Audit evidence is recorded in `docs/audit-2026-08-23.md` against revision `f9d4365`.
- `spikes/pwa-local-engine/build-browser.mjs` hard-codes its source module array without `fullscreen.js`; `src/cantracediag/web/index.html` loads that module and exposes the fullscreen controls. A generated bundle contains no `fullscreen` reference, so the deployed control has no behavior.
- `.github/workflows/ci.yml` runs unit tests, the build, file/HTTP checks, and a MIME check, but does not invoke `spikes/pwa-local-engine/browser-smoke.mjs`, which tests generated-site service-worker and workspace behavior. This leaves the delivered browser application untested by CI.
- `.dockerignore` excludes `.venv` but not `.pydeps`; the measured repository Docker context is about 933 MB and `.pydeps` accounts for about 383 MB.
- The audit also found text-marker rewriting in `build-browser.mjs`, production source retained under `spikes/`, stale Logics workflow records, mutable or inconsistent release pins, a `StarletteDeprecationWarning` from `tests/conftest.py`, and release validation that is less self-contained than CI.
- Re-run on 2026-08-23: `.venv/bin/ruff check .` passed; `.venv/bin/pytest -q` passed 166 tests with one Starlette deprecation warning; `node --experimental-strip-types --test spikes/pwa-local-engine/tests/*.test.ts` passed 27 tests; the PWA build, `logics-manager lint --require-status`, and `logics-manager audit --group-by-doc` passed (audit: 0 blocking issues, 22 deferred warnings).
- This request captures candidates only. It intentionally creates no backlog item, task, product brief, or implementation commitment.

# Acceptance criteria
- AC1: Any scoped remediation ensures every product web module required by the HTML shell is included in the generated PWA bundle, with a regression test that fails when the module set diverges.
- AC2: Any scoped remediation runs a generated-site browser smoke test in both pull-request CI and release validation, including an observable fullscreen-control check.
- AC3: Any scoped remediation reduces the Docker build context by excluding local dependency caches and other non-production sources without removing required build inputs.
- AC4: Later scoped work explicitly decides the disposition of the fragile PWA text-rewrite architecture, obsolete spike material, stale workflow records, supply-chain pinning, the test-client deprecation, and release-validation parity.
- AC5: Scope boundaries are explicit: this review does not change product code, alter deployment, or close existing workflow documents.

# Definition of Ready (DoR)
- [x] Problem statement is explicit and user impact is clear.
- [x] Scope boundaries (in/out) are explicit.
- [x] Acceptance criteria are testable.
- [x] Dependencies and known risks are listed.

# Companion docs
- Product brief(s): (none yet)
- Architecture decision(s): (none yet)

# References
- `docs/audit-2026-08-23.md`
- `spikes/pwa-local-engine/build-browser.mjs`
- `src/cantracediag/web/index.html`
- `.github/workflows/ci.yml`
- `.github/workflows/release.yml`
- `.dockerignore`
- `spikes/pwa-local-engine/browser-smoke.mjs`
- `tests/conftest.py`

# Backlog
- none
