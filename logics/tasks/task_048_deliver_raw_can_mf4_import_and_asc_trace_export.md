## task_048_deliver_raw_can_mf4_import_and_asc_trace_export - Deliver raw CAN MF4 import and ASC trace export
> From version: 1.0.0
> Schema version: 1.0
> Status: Ready
> Understanding: 90%
> Confidence: 85%
> Progress: 0%
> Complexity: High
> Theme: Raw CAN trace interoperability
> Reminder: Update status/understanding/confidence/progress and linked request/backlog references when you edit this doc.
> Indicators reviewed: 2026-10-01 14:28:02

# AI Context
Implement the three linked slices in waves: independent sample characterization, MF4 adapter, stored-frame ASC writer/API, then UI and full round-trip evidence. The external sample must never be modified or committed. Documentation scaffolding alone does not satisfy delivery or closeout.

# Context
- Deliver raw classic-CAN MDF4 import and raw ASC export through the linked request and three implementation slices.
- Sample evidence is in logics/external/mf4_sample_inspection.md; operational recordings remain external.
- All slices have High priority: characterize/import first, raw writer second, UI integration third. The writer can be exercised independently on existing traces.

# Plan
- [ ] 1. Wave 1: Read the sample inspection note, characterize the unfinished layout with an independent MDF reader, freeze source hash/count/value evidence and supported-layout/dependency/ordering contracts; generate synthetic fixtures before product changes.
- [ ] 2. Wave 2: Deliver and validate the MF4 adapter, safe read-only recovery, server/CLI dispatch, explicit diagnostics, memory behavior and early cancellation; prove sample-like unfinished files are not treated as empty.
- [ ] 3. Wave 3: Deliver the stored-frame iterator and streaming ASC serializer/API, with provenance policy, all three time scopes, exclusion metadata and round-trip tests independent of signals/DBC.
- [ ] 4. Wave 4: Deliver server UI import/export capability, static-PWA rejection, support documentation and complete synthetic end-to-end plus ASC/TRC/BLF and signal-export regression checks.
- [ ] 5. Wave 5: Manually verify the external sample through MF4 import, ASC download and re-import; reconcile structural baseline with independent-reader results, compare counts/normalized values, confirm source hash unchanged and record evidence without committing recording or payloads.
- [ ] 6. Wave 6: Run required lint/tests and Logics checks, update traceability and closeout proof. During implementation follow repository release policy: implementation commit, next SemVer preparation commit, push and CI on exact version SHA, annotated tag, release-workflow verification and evidence. Do not execute implementation/release while only scaffolding this corpus.
- [ ] ADR 009 checkpoint: update affected Logics docs during each meaningful wave and leave the repo commit-ready.
- [ ] Keep commit creation under operator control; do not force one commit per micro-step.
- [ ] GATE: do not close until lint, audit, and scaffold validation pass.

# Backlog
- `item_057_import_third_party_raw_can_mf4_including_unfinished_recordings`
- `item_058_stream_stored_raw_can_frames_to_round_trip_safe_asc_exports`
- `item_059_expose_mf4_import_and_raw_asc_download_with_explicit_server_capability`

# Definition of Done (DoD)
- [ ] All request acceptance criteria and linked slice criteria have implementation evidence and meaningful automated coverage.
- [ ] Supported finalized and sample-like unfinished MDF4 files import safely with correct raw values, diagnostics and source-preserving recovery.
- [ ] Full, inclusive A/B and visible ASC exports work without DBC/signals, preserve raw values and satisfy the timestamp round-trip tolerance.
- [ ] External sample results are independently verified and MF4 -> ASC -> ASC re-import comparisons recorded with unchanged source hash.
- [ ] Reader/export memory and import cancellation are measured on representative generated large inputs.
- [ ] Server UI, API and CLI support agree; static PWA clearly rejects unsupported capabilities; documentation and regression checks pass.
- [ ] Logics traceability, lint/audit and required implementation/release evidence are recorded before closeout.

# AC Traceability
- request-AC1 -> `item_057_import_third_party_raw_can_mf4_including_unfinished_recordings`. Proof deferred to slice closeout.
- request-AC2 -> `item_057_import_third_party_raw_can_mf4_including_unfinished_recordings`. Proof deferred to slice closeout.
- request-AC3 -> `item_057_import_third_party_raw_can_mf4_including_unfinished_recordings`. Proof deferred to slice closeout.
- request-AC4 -> `item_057_import_third_party_raw_can_mf4_including_unfinished_recordings`. Proof deferred to slice closeout.
- request-AC5 -> `item_057_import_third_party_raw_can_mf4_including_unfinished_recordings`. Proof deferred to slice closeout.
- request-AC9 -> `item_057_import_third_party_raw_can_mf4_including_unfinished_recordings`. Proof deferred to slice closeout.
- request-AC6 -> `item_058_stream_stored_raw_can_frames_to_round_trip_safe_asc_exports`. Proof deferred to slice closeout.
- request-AC7 -> `item_058_stream_stored_raw_can_frames_to_round_trip_safe_asc_exports`. Proof deferred to slice closeout.
- request-AC8 -> `item_058_stream_stored_raw_can_frames_to_round_trip_safe_asc_exports`. Proof deferred to slice closeout.
- request-AC9 -> `item_058_stream_stored_raw_can_frames_to_round_trip_safe_asc_exports`. Proof deferred to slice closeout.
- request-AC1 -> `item_059_expose_mf4_import_and_raw_asc_download_with_explicit_server_capability`. Proof deferred to slice closeout.
- request-AC6 -> `item_059_expose_mf4_import_and_raw_asc_download_with_explicit_server_capability`. Proof deferred to slice closeout.
- request-AC7 -> `item_059_expose_mf4_import_and_raw_asc_download_with_explicit_server_capability`. Proof deferred to slice closeout.
- request-AC8 -> `item_059_expose_mf4_import_and_raw_asc_download_with_explicit_server_capability`. Proof deferred to slice closeout.
- request-AC9 -> `item_059_expose_mf4_import_and_raw_asc_download_with_explicit_server_capability`. Proof deferred to slice closeout.
- request-AC10 -> `item_059_expose_mf4_import_and_raw_asc_download_with_explicit_server_capability`. Proof deferred to slice closeout.

# Validation
- Implementation not started; these checks are required during delivery.
- Run focused MF4 adapter, raw ASC serializer, pipeline/store, API and UI tests using synthetic finalized/unfinished fixtures, then `.venv/bin/ruff check .` and `.venv/bin/pytest`.
- Run the repository browser/PWA checks for changed capability and export flows; record the exact commands and results.
- Run the external-sample manual round trip from the inspection note and record counts, ID/payload/channel/direction comparisons, timestamp error and source hash.
- Measure large generated input peak memory, progress and initialization/ingestion cancellation.
- Run `logics-manager flow validate req_033_read_raw_can_mf4_recordings_and_save_traces_as_asc`, `logics-manager lint --require-status` and `logics-manager audit --legacy-cutoff-version 1.1.0 --group-by-doc`.

# Report
- Not started.

# Links
- Request: `req_033_read_raw_can_mf4_recordings_and_save_traces_as_asc`
- Product brief(s): `prod_016_raw_mf4_can_import_and_interoperable_asc_trace_export`
- Architecture decision(s): (none yet)
