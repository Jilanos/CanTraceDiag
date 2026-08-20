## task_041_deliver_concise_multi_dbc_explorer_navigation - Deliver concise multi-DBC explorer navigation
> From version: 1.0.0
> Schema version: 1.0
> Status: Ready
> Understanding: 95%
> Confidence: 90%
> Progress: 0%
> Complexity: Medium
> Theme: Implementation delivery
> Reminder: Update status/understanding/confidence/progress and linked request/backlog references when you edit this doc.

# AI Context
- Summary: (unfilled: replace before this doc is used)
- Keywords: deliver, concise, multi, dbc, explorer, navigation
- Use when: (unfilled: replace before this doc is used)
- Skip when: (unfilled: replace before this doc is used)

# Context
- Orchestrate the scaffolded request chain and keep sibling implementation slices linked.

# Plan
- [ ] 1. Map the server and local-PWA signal metadata needed to identify trace-used, active, and unused DBCs without changing decoding behavior.
- [ ] 2. Implement the relevant-DBC default and the compact on-demand unused-DBC control with accessible state semantics.
- [ ] 3. Add search-aware DBC counts and message-level expandable sections while preserving existing filters and selected plots.
- [ ] 4. Align styling for dense desktop and supported narrow viewports, keeping controls compact and keyboard reachable.
- [ ] 5. Add focused multi-DBC browser and local-PWA coverage, validate the project, and record closeout evidence.
- [ ] 6. After implementation validation, prepare the next SemVer version in all canonical version surfaces and commit the version preparation.
- [ ] 7. Push the version-preparation commit, wait for CI to pass on that exact SHA, then create and push one annotated `vX.Y.Z` tag.
- [ ] 8. Verify the tag-triggered validate, publish, deploy, and GitHub release workflow; record the implementation SHA, CI run URL, tag, and outcome in the task closeout.
- [ ] ADR 009 checkpoint: update affected Logics docs during each meaningful wave and leave the repo commit-ready.
- [ ] Keep commit creation under operator control; do not force one commit per micro-step.
- [ ] GATE: do not close until lint, audit, and scaffold validation pass.

# Backlog
- `item_042_prioritize_relevant_dbcs_and_add_message_level_signal_navigation`

# Definition of Done (DoD)
- [ ] Generated request, product, backlog, and task docs are present.
- [ ] Context-pack handoff is available when requested.
- [ ] Validation passes.
- [ ] Meaningful waves followed ADR 009: affected docs updated and the repo left commit-ready without automatic commits.
- [ ] The release policy was completed: no force-push or retagging; CI passed before tagging; tag-triggered publication, deployment, and GitHub release were verified with recorded evidence.

# AC Traceability
- request-AC1 -> `item_042_prioritize_relevant_dbcs_and_add_message_level_signal_navigation`. Proof deferred to slice closeout.
- request-AC2 -> `item_042_prioritize_relevant_dbcs_and_add_message_level_signal_navigation`. Proof deferred to slice closeout.
- request-AC3 -> `item_042_prioritize_relevant_dbcs_and_add_message_level_signal_navigation`. Proof deferred to slice closeout.
- request-AC4 -> `item_042_prioritize_relevant_dbcs_and_add_message_level_signal_navigation`. Proof deferred to slice closeout.
- request-AC5 -> `item_042_prioritize_relevant_dbcs_and_add_message_level_signal_navigation`. Proof deferred to slice closeout.

# Validation
- (no validation recorded yet)

# Report
- Not started.

# Links
- Request: `req_022_streamline_navigation_of_large_multi_dbc_signal_catalogs`
- Product brief(s): `prod_009_efficient_multi_dbc_signal_exploration`
- Architecture decision(s): (none yet)
