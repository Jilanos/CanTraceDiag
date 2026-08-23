## task_045_deliver_static_pwa_delivery_and_release_hardening - Deliver static PWA delivery and release hardening
> From version: 1.0.0
> Schema version: 1.0
> Status: In progress
> Understanding: 90%
> Confidence: 85%
> Progress: 0%
> Complexity: Medium
> Theme: Implementation delivery
> Reminder: Update status/understanding/confidence/progress and linked request/backlog references when you edit this doc.
> Indicators reviewed: 2026-08-23 09:50:36
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
- request-AC1 -> `item_049_prevent_static_pwa_module_omissions_and_restore_fullscreen_delivery`. Proof deferred to slice closeout.
- request-AC2 -> `item_049_prevent_static_pwa_module_omissions_and_restore_fullscreen_delivery`. Proof deferred to slice closeout.
- request-AC6 -> `item_049_prevent_static_pwa_module_omissions_and_restore_fullscreen_delivery`. Proof deferred to slice closeout.
- request-AC2 -> `item_050_run_generated_site_browser_smoke_in_ci_and_release_validation`. Proof deferred to slice closeout.
- request-AC3 -> `item_050_run_generated_site_browser_smoke_in_ci_and_release_validation`. Proof deferred to slice closeout.
- request-AC6 -> `item_050_run_generated_site_browser_smoke_in_ci_and_release_validation`. Proof deferred to slice closeout.
- request-AC4 -> `item_051_shrink_docker_build_context_for_the_static_pwa_image`. Proof deferred to slice closeout.
- request-AC6 -> `item_051_shrink_docker_build_context_for_the_static_pwa_image`. Proof deferred to slice closeout.
- request-AC5 -> `item_052_resolve_residual_audit_governance_and_release_hardening_debt`. Proof deferred to slice closeout.
- request-AC6 -> `item_052_resolve_residual_audit_governance_and_release_hardening_debt`. Proof deferred to slice closeout.

# Validation
- (no validation recorded yet)

# Report
- Not started.

# Links
- Request: `req_028_harden_static_pwa_delivery_and_release_validation`
- Product brief(s): `prod_013_reliable_static_pwa_delivery`
- Architecture decision(s): (none yet)
