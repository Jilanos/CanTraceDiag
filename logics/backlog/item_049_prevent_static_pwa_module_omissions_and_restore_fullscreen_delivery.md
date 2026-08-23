## item_049_prevent_static_pwa_module_omissions_and_restore_fullscreen_delivery - Prevent static PWA module omissions and restore fullscreen delivery
> From version: 1.0.0
> Schema version: 1.0
> Status: In progress
> Understanding: 90%
> Confidence: 85%
> Progress: 90%
> Complexity: Medium
> Theme: PWA bundle integrity
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.
> Indicators reviewed: 2026-08-23 09:50:36

# AI Context
- Summary: Fix the audited static PWA module omission by making the generated bundle track source shell scripts and restoring delivered fullscreen behavior.
- Keywords: prevent, static, pwa, module, omissions, restore, fullscreen, delivery
- Use when: Changing `build-browser.mjs`, source shell script discovery, or fullscreen delivery tests.
- Skip when: Only changing CI scheduling, Docker context, or broader release governance without touching bundle completeness.

# Problem
- The production PWA build duplicates the source shell script order in a hard-coded list, and the reviewed list omitted `fullscreen.js`.
- A visible documented control can therefore ship without behavior while existing tests remain green.

# Scope
- In:
  - Derive the product module list from the source HTML shell or fail the build when the declared scripts and bundled modules diverge.
  - Preserve the required JavaScript execution order when assembling the generated PWA bundle.
  - Restore the delivered fullscreen controller in the generated artifact and keep unsupported or refused fullscreen requests visible to the user.
  - Add focused tests that fail when a product web module loaded by `src/cantracediag/web/index.html` is absent from the generated PWA bundle.
  - Verify the generated artifact contains and serves the fullscreen controller behavior.
- Out:
  - Changing the fullscreen UX beyond restoring the documented delivered behavior.
  - Moving the PWA out of `spikes/` or replacing the transport abstraction as part of this slice.
  - Changing Python/FastAPI behavior except where a shared fixture is needed for verification.

# Acceptance criteria
- AC1: The build reads or validates the product script list from `src/cantracediag/web/index.html`, including `fullscreen.js`, and preserves the source script order.
- AC2: A regression test fails if any product `web/js` module referenced by the source shell is missing from the generated bundle or generated site.
- AC3: The built site contains the fullscreen control implementation, and the browser smoke can observe a click path that either enters fullscreen or reports a supported refusal state.
- AC4: Existing Node PWA tests and the PWA build remain green after the change.

# AC Traceability
- request-AC1 -> This backlog slice. Proof: AC1: The build reads or validates the product script list from `src/cantracediag/web/index.html`, including `fullscreen.js`, and preserves the source script order.
- request-AC2 -> This backlog slice. Proof: AC2: A regression test fails if any product `web/js` module referenced by the source shell is missing from the generated bundle or generated site.
- request-AC6 -> This backlog slice. Proof: AC3: The built site contains the fullscreen control implementation, and the browser smoke can observe a click path that either enters fullscreen or reports a supported refusal state.

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
