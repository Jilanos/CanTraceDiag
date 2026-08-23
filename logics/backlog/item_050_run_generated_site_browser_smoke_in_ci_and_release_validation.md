## item_050_run_generated_site_browser_smoke_in_ci_and_release_validation - Run generated-site browser smoke in CI and release validation
> From version: 1.0.0
> Schema version: 1.0
> Status: In progress
> Understanding: 90%
> Confidence: 85%
> Progress: 10%
> Complexity: Medium
> Theme: Delivered-browser automation
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.
> Indicators reviewed: 2026-08-23 09:50:36

# AI Context
- Summary: Wire the generated-site browser smoke into PR and release validation so delivered PWA behavior is checked automatically.
- Keywords: run, generated, site, browser, smoke, release, validation
- Use when: Updating GitHub Actions or smoke-test coverage for the built static PWA artifact.
- Skip when: Fixing product logic that is already covered by lower-level Node or Python tests.

# Problem
- `spikes/pwa-local-engine/browser-smoke.mjs` validates generated-site behavior but is not invoked by CI or release validation.
- Release validation currently repeats less than CI, making the release gate depend on external assumptions about prior push validation.

# Scope
- In:
  - Make the generated-site browser smoke deterministic and suitable for CI execution if any environment setup is currently implicit.
  - Add the browser smoke to the pull-request PWA workflow after the generated site is built and served.
  - Add equivalent generated-site browser smoke coverage to release validation, alongside the static build and Node tests.
  - Extend the smoke to cover the restored fullscreen control at a behavior level that remains stable in headless Chromium.
  - Document any required browser or Playwright dependency setup in the workflow rather than relying on a developer machine state.
- Out:
  - Replacing unit tests with browser-only checks.
  - Adding large fixture uploads or long-running performance tests to the default CI path.
  - Changing release publishing, tagging, or deployment semantics beyond validation coverage.

# Acceptance criteria
- AC1: Pull-request CI runs the generated-site browser smoke on the built PWA artifact and fails on delivered app-shell, service-worker, workspace-persistence, or fullscreen-control regressions.
- AC2: Release validation runs the same generated-site smoke before publication steps and records the check in release evidence.
- AC3: Workflow setup installs or reuses the required browser runtime deterministically on GitHub-hosted runners.
- AC4: Local validation commands for the browser smoke are documented in the task closeout and pass with the rest of the standard suite.

# AC Traceability
- request-AC2 -> This backlog slice. Proof: AC1: Pull-request CI runs the generated-site browser smoke on the built PWA artifact and fails on delivered app-shell, service-worker, workspace-persistence, or fullscreen-control regressions.
- request-AC3 -> This backlog slice. Proof: AC2: Release validation runs the same generated-site smoke before publication steps and records the check in release evidence.
- request-AC6 -> This backlog slice. Proof: AC3: Workflow setup installs or reuses the required browser runtime deterministically on GitHub-hosted runners.

# Decision framing
- Product framing: Not needed
- Architecture framing: Not needed

# Links
- Product brief(s): `prod_013_reliable_static_pwa_delivery`
- Architecture decision(s): (none yet)
- Request: `req_028_harden_static_pwa_delivery_and_release_validation`
- Primary task(s): `task_045_deliver_static_pwa_delivery_and_release_hardening`

# Priority
- Priority: High
- Rationale: Set by scaffold input or defaulted for grooming.
