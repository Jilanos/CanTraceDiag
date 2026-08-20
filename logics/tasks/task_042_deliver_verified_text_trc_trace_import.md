## task_042_deliver_verified_text_trc_trace_import - Deliver verified text TRC trace import
> From version: 1.0.0
> Schema version: 1.0
> Status: Ready
> Understanding: 90%
> Confidence: 85%
> Progress: 0%
> Complexity: Medium
> Theme: Implementation delivery
> Reminder: Update status/understanding/confidence/progress and linked request/backlog references when you edit this doc.

# AI Context
- Summary: Deliver direct classic-CAN text .trc ingestion across both import surfaces with test-backed normalization and diagnostics.
- Keywords: deliver, verified, text, trc, trace, import
- Use when: Executing the parser, import-surface parity, fixtures, and validation waves for this request.
- Skip when: Starting a separate format family or a CAN FD/CAN XL capability.

# Context
- Orchestrate the scaffolded request chain and keep sibling implementation slices linked.

# Plan
- [ ] 1. Characterize the supplied trace layout and define the supported v1.1 classic-CAN grammar, normalization rules, and explicit diagnostics for unsupported records.
- [ ] 2. Implement streaming server-side format dispatch and the TRC reader while retaining current pipeline progress, cancellation, DBC decoding, and storage contracts.
- [ ] 3. Implement equivalent local-PWA format dispatch and parsing, then expose both supported extensions consistently in product copy and file pickers.
- [ ] 4. Add focused fixtures and automated coverage for valid frames, edge cases, diagnostics, API/UI import, local-PWA parity, and ASC non-regression.
- [ ] 5. Validate the project and record closeout evidence.
- [ ] 6. Follow the release policy after implementation: prepare the next SemVer version, push the version-preparation commit, wait for CI on that exact SHA, create and push the annotated tag, verify the tag-triggered publication/deployment workflow, and record all release evidence.
- [ ] ADR 009 checkpoint: update affected Logics docs during each meaningful wave and leave the repo commit-ready.
- [ ] Keep commit creation under operator control; do not force one commit per micro-step.
- [ ] GATE: do not close until lint, audit, and scaffold validation pass.

# Backlog
- `item_043_add_verified_text_trc_import_with_server_and_local_pwa_parity`

# Definition of Done (DoD)
- [ ] Generated request, product, backlog, and task docs are present.
- [ ] Context-pack handoff is available when requested.
- [ ] Validation passes.
- [ ] Meaningful waves followed ADR 009: affected docs updated and the repo left commit-ready without automatic commits.

# AC Traceability
- request-AC1 -> `item_043_add_verified_text_trc_import_with_server_and_local_pwa_parity`. Proof deferred to slice closeout.
- request-AC2 -> `item_043_add_verified_text_trc_import_with_server_and_local_pwa_parity`. Proof deferred to slice closeout.
- request-AC3 -> `item_043_add_verified_text_trc_import_with_server_and_local_pwa_parity`. Proof deferred to slice closeout.
- request-AC4 -> `item_043_add_verified_text_trc_import_with_server_and_local_pwa_parity`. Proof deferred to slice closeout.
- request-AC5 -> `item_043_add_verified_text_trc_import_with_server_and_local_pwa_parity`. Proof deferred to slice closeout.

# Validation
- (no validation recorded yet)

# Report
- Not started.

# Links
- Request: `req_023_import_text_trc_can_trace_recordings`
- Product brief(s): `prod_010_interoperable_classic_can_trace_import`
- Architecture decision(s): (none yet)
