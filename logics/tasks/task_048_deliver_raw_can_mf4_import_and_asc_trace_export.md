## task_048_deliver_raw_can_mf4_import_and_asc_trace_export - Deliver raw CAN MF4 import and ASC trace export
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 95%
> Confidence: 95%
> Progress: 100%
> Complexity: High
> Theme: Raw CAN trace interoperability
> Reminder: Update status/understanding/confidence/progress and linked request/backlog references when you edit this doc.
> Indicators reviewed: 2026-10-01 15:16:35
> Owner: claude

# AI Context
Implement the three linked slices in waves: independent sample characterization, MF4 adapter, stored-frame ASC writer/API, then UI and full round-trip evidence. The external sample must never be modified or committed. Documentation scaffolding alone does not satisfy delivery or closeout.

# Context
- Deliver raw classic-CAN MDF4 import and raw ASC export through the linked request and three implementation slices.
- Sample evidence is in logics/external/mf4_sample_inspection.md; operational recordings remain external.
- All slices have High priority: characterize/import first, raw writer second, UI integration third. The writer can be exercised independently on existing traces.

# Plan
- [x] 1. Wave 1: Read the sample inspection note, characterize the unfinished layout with an independent MDF reader, freeze source hash/count/value evidence and supported-layout/dependency/ordering contracts; generate synthetic fixtures before product changes.
- [x] 2. Wave 2: Deliver and validate the MF4 adapter, safe read-only recovery, server/CLI dispatch, explicit diagnostics, memory behavior and early cancellation; prove sample-like unfinished files are not treated as empty.
- [x] 3. Wave 3: Deliver the stored-frame iterator and streaming ASC serializer/API, with provenance policy, all three time scopes, exclusion metadata and round-trip tests independent of signals/DBC.
- [x] 4. Wave 4: Deliver server UI import/export capability, static-PWA rejection, support documentation and complete synthetic end-to-end plus ASC/TRC/BLF and signal-export regression checks.
- [x] 5. Wave 5: Manually verify the external sample through MF4 import, ASC download and re-import; reconcile structural baseline with independent-reader results, compare counts/normalized values, confirm source hash unchanged and record evidence without committing recording or payloads.
- [x] 6. Wave 6: Run required lint/tests and Logics checks, update traceability and closeout proof. During implementation follow repository release policy: implementation commit, next SemVer preparation commit, push and CI on exact version SHA, annotated tag, release-workflow verification and evidence. Do not execute implementation/release while only scaffolding this corpus.
- [x] ADR 009 checkpoint: update affected Logics docs during each meaningful wave and leave the repo commit-ready.
- [x] Keep commit creation under operator control; do not force one commit per micro-step.
- [x] GATE: do not close until lint, audit, and scaffold validation pass.

# Backlog
- `item_057_import_third_party_raw_can_mf4_including_unfinished_recordings`
- `item_058_stream_stored_raw_can_frames_to_round_trip_safe_asc_exports`
- `item_059_expose_mf4_import_and_raw_asc_download_with_explicit_server_capability`

# Definition of Done (DoD)
- [x] All request acceptance criteria and linked slice criteria have implementation evidence and meaningful automated coverage.
- [x] Supported finalized and sample-like unfinished MDF4 files import safely with correct raw values, diagnostics and source-preserving recovery.
- [x] Full, inclusive A/B and visible ASC exports work without DBC/signals, preserve raw values and satisfy the timestamp round-trip tolerance.
- [x] External sample results are independently verified and MF4 -> ASC -> ASC re-import comparisons recorded with unchanged source hash.
- [x] Reader/export memory and import cancellation are measured on representative generated large inputs.
- [x] Server UI, API and CLI support agree; static PWA clearly rejects unsupported capabilities; documentation and regression checks pass.
- [x] Logics traceability, lint/audit and required implementation/release evidence are recorded before closeout.

# AC Traceability
- request-AC1 -> `item_057_import_third_party_raw_can_mf4_including_unfinished_recordings`, `item_059_expose_mf4_import_and_raw_asc_download_with_explicit_server_capability`. Proof: implemented in 273cdd6 (`TRACE_SUFFIXES` + upload guard in `api.py`, `.mf4` dispatch in `pipeline.py`, CLI help) and 00c27c9 (picker `accept=".asc,.trc,.blf,.mf4"`); `tests/test_mf4.py::test_upload_accepts_an_upper_case_mf4`, `test_path_import_accepts_an_mf4`, `test_a_truncated_mf4_upload_keeps_the_loaded_trace` (size/temp-store path unchanged, previous trace kept, no path echoed), `tests/test_e2e_ui.py::test_mf4_imports_and_downloads_as_raw_asc_without_signals` (real picker), `cantracediag info` on the external sample.
- request-AC2 -> `item_057_import_third_party_raw_can_mf4_including_unfinished_recordings`. Proof: implemented in 273cdd6 (`src/cantracediag/formats/mf4.py`); `test_raw_frames_are_normalized_without_a_dbc` (relative seconds, buses 1/2/9, standard/extended, DLC 0/8, exact payload, Rx/Tx), `test_missing_provenance_stays_unknown` (no channel/direction invented, IDE fallback), `test_mf4_import_without_dbc_keeps_every_frame`; no DBC is read from the MF4.
- request-AC3 -> `item_057_import_third_party_raw_can_mf4_including_unfinished_recordings`. Proof: recovery in an adapter-owned temporary copy plus independent DT-to-EOF reconciliation (273cdd6); `test_recovery_never_modifies_the_source`, `test_zero_cycle_counters_never_produce_an_empty_import`, `test_unfinished_and_finalized_layouts_read_identically`, `test_payload_that_mimics_a_block_header_cannot_shorten_recovery`; external sample independently verified (asammdf counts 775/116,838/184 = 117,797 and raw-byte decode field-for-field equal), source SHA-256 unchanged — see `logics/external/mf4_sample_inspection.md`.
- request-AC4 -> `item_057_import_third_party_raw_can_mf4_including_unfinished_recordings`. Proof: chronological merge with (group, record) ties documented in `formats/mf4.py`; `test_groups_merge_chronologically_with_documented_ties`, `test_time_going_backwards_in_a_group_is_reported`, `test_unsupported_and_malformed_records_are_diagnosed_not_dropped` (FD, remote, error, LIN, DLC>8, DataLength≠DLC), `test_a_truncated_recording_fails_before_yielding_anything`, `test_non_mf4_content_is_rejected`.
- request-AC5 -> `item_057_import_third_party_raw_can_mf4_including_unfinished_recordings`. Proof: `test_mf4_frames_decode_against_the_shared_dbc_decoder`, `test_signal_export_contract_is_unchanged`, `test_path_import_accepts_an_mf4` (report), `test_mf4_import_reports_monotonic_progress`, `test_cancellation_during_initialization`, `test_cancellation_during_record_ingestion`, `test_chunked_reading_matches_a_single_read`; large-input measurements (2M/4M records: adapter +20 B/record, cancel latency ≤0.03 s) in Validation.
- request-AC6 -> `item_058_stream_stored_raw_can_frames_to_round_trip_safe_asc_exports`, `item_059_expose_mf4_import_and_raw_asc_download_with_explicit_server_capability`. Proof: implemented in cc48d6b (`export.raw_asc`, `TraceStore.iter_raw_frames`, `POST /api/export-asc`); `tests/test_raw_asc_export.py::test_download_needs_no_dbc_and_no_signals`, `test_mf4_round_trips_through_asc_without_a_dbc`, `test_existing_formats_round_trip_through_asc[sample.asc|sample.trc|sample_dec.asc|blf]`, `test_python_can_reads_the_export`, `test_signal_export_contract_is_unchanged`.
- request-AC7 -> `item_058_stream_stored_raw_can_frames_to_round_trip_safe_asc_exports`, `item_059_expose_mf4_import_and_raw_asc_download_with_explicit_server_capability`. Proof: `test_line_grammar`, `test_iterator_orders_by_time_then_seq_with_inclusive_bounds`, `test_ranged_scopes_are_inclusive_and_ignore_signal_state[between_ab|visible]`, `test_unknown_provenance_blocks_until_explicitly_assumed`, `test_unknown_provenance_is_refused_unless_explicitly_assumed`; sample A/B 100–110 s export = 18,683 stored frames.
- request-AC8 -> `item_058_stream_stored_raw_can_frames_to_round_trip_safe_asc_exports`, `item_059_expose_mf4_import_and_raw_asc_download_with_explicit_server_capability`. Proof: `test_timestamp_round_trip_error_stays_within_one_microsecond` (≤0.5 µs), round-trip tests above (count/ID/IDE/channel/direction/DLC/payload exact), `test_summary_discloses_exclusions_before_download`, `test_header_discloses_scope_exclusions_assumptions_and_warnings`; external sample round trip 117,797 frames, 0 mismatches, 0 s error.
- request-AC9 -> all three slices. Proof: generated fixtures (`tests/mf4_fixture.py`, finalized and unfinished) in `tests/test_mf4.py` (32), `tests/test_raw_asc_export.py` (26) and the e2e scenario cover interleaving, equal times, sparse buses, std/ext, DLC 0/8, unsupported types, recovery, truncation, empty data, ranges, restore (`test_export_works_on_a_restored_session`), no-DBC/no-signal, batching, cancellation and ASC/TRC/BLF + CSV regression; full suite 305 passed; the sample stayed outside git.
- request-AC10 -> `item_059_expose_mf4_import_and_raw_asc_download_with_explicit_server_capability`. Proof: implemented in 00c27c9; `product-bundle.test.ts` ("does not offer BLF or MF4 …", "does not offer the server-only raw ASC export …"), `local-backend.test.ts` ("names server mode …", "rejects an MF4 selection before reading the file", "advertises no server capability and refuses raw ASC export"), PWA smoke `ok: true`; server dialog separates raw ASC from signal export with scopes, empty state, exclusions and `.asc` naming (e2e scenario, `test_empty_range_gives_a_valid_header_only_asc`).

# Validation
- `.venv/bin/ruff check .` -> All checks passed.
- `.venv/bin/pytest` -> 305 passed (includes 34 Playwright server-UI tests; new: `tests/test_mf4.py` 32, `tests/test_raw_asc_export.py` 26, MF4 -> raw ASC e2e scenario).
- `node --experimental-strip-types --test spikes/pwa-local-engine/tests/*.test.ts` -> 86 passed; `node spikes/pwa-local-engine/build-browser.mjs` -> built; generated `site/index.html` contains no `.mf4` / `asc_raw`.
- `CTD_ENGINE_ROOT=spikes/pwa-local-engine/site CTD_ENGINE_PORT=9880 CTD_ENGINE_DEBUG_PORT=9230 node spikes/pwa-local-engine/browser-smoke.mjs` -> exit 0, `"ok": true`.
- External sample, manual (outside git): upload -> `POST /api/export-asc` -> ASC re-upload: 117,797 frames each way, 0 field mismatches, max timestamp error 0 s, A/B 100-110 s = 18,683 frames as stored; source SHA-256 e00a995c...cd03099 unchanged. Details in `logics/external/mf4_sample_inspection.md`.
- Large generated unfinalized MF4 (single DT, 3 interleaved groups), fresh process per measurement, peak RSS: import baseline 163 MB; adapter iteration 197 MB (2M records, 42 MB) / 237 MB (4M, 84 MB) -> ~20 B/record growth = asammdf record-offset index for an unsorted data group, frames not materialized (~200 B/record if they were); MF4 import into DuckDB 629 / 778 MB (ASC import of the same 2M frames: 584 MB); raw ASC export 447 / 669 MB (DuckDB ORDER BY; Python side streams 8,192-row batches). Time to first record 0.49 s on 84 MB; cancellation requested at 0.2 / 1.0 / 3.0 s stopped within 0.03 s (initialization and ingestion).
- Logics: `logics-manager flow validate req_033_read_raw_can_mf4_recordings_and_save_traces_as_asc`, `logics-manager lint --require-status`, `logics-manager audit --legacy-cutoff-version 1.1.0 --group-by-doc` -> see closeout.
- command: `.venv/bin/ruff check . && .venv/bin/python -m pytest && node --experimental-strip-types --test spikes/pwa-local-engine/tests/*.test.ts && node spikes/pwa-local-engine/build-browser.mjs && node spikes/pwa-local-engine/browser-smoke.mjs` | result: passed | date: 2026-10-01 | note: 305 pytest (34 E2E), 86 node, PWA smoke ok; CI 36866700295 and release workflow 36867048417 green for v1.3.0
- Finish workflow executed on 2026-10-01.
- Linked backlog/request close verification passed.

# Report
- Commits: `273cdd6` MF4 import (adapter, pipeline/API/CLI acceptance, persisted import warnings, fixtures/tests); `cc48d6b` raw ASC export (store iterator + summary, serializer, `/api/export-asc[/summary]`, `cantracediag export-asc`); `00c27c9` server UI + static PWA boundary; `33c1a4c` docs.
- Dependency: `asammdf>=8.8.27,<9` (LGPL-3.0-or-later, unmodified library dependency; installed 8.8.27). Imported lazily behind `formats/mf4.py`; nothing from it reaches downstream code.
- Supported layout: MDF 4.x ASAM bus logging with `CAN_DataFrame` groups (stored or virtual `BusChannel`/`IDE`/`Dir`, `DataLength` via conversion). Unfinalized files are recovered only by asammdf in an adapter-owned temporary copy, then reconciled independently (DT-to-EOF bytes == complete records); unfinalized DL/DZ layouts or populated VLSD groups are refused rather than guessed.
- Ordering contract: chronological k-way merge; ties by (channel-group index, record index) because asammdf does not expose cross-group interleaving; a group whose time goes backwards is reported as a warning and the store still orders by (timestamp_s, seq).
- Provenance policy: ASC export blocks frames without a numeric channel or Rx/Tx direction (HTTP 409 / CLI exit 2) unless `assume` is chosen; then channel 1 / Rx is written and disclosed in the header and summary.
- Found and fixed on the way: a stale `/api/import-job` poll could overwrite the rendered import summary (would have hidden the recovery warning); export-dialog rows ignored the `hidden` attribute.
- Reserves (not affecting the verdicts above): adapter memory grows ~20 B/record with asammdf's offset index for unsorted data groups; raw ASC export memory is bounded on the Python side but DuckDB's sort scales with the exported rows (spills under its memory limit); the ASC `date` header carries the export time (disclosed in a comment) because the source start time is not stored.
- Release v1.3.0 (operator-authorized): preparation commit `13bb1e7`, pushed to origin/main; CI run 36866700295 green (pwa, test 3.11, test 3.12); annotated tag `v1.3.0` on `13bb1e7`; release workflow 36867048417 green (validate, validate-python, publish, deploy, release); GitHub release https://github.com/Jilanos/CanTraceDiag/releases/tag/v1.3.0 published 2026-10-01T13:15:40Z. Evidence in `logics/release/evidence.jsonl`; `logics-manager release validate 1.3.0` passes every gate.
- Finished on 2026-10-01.
- Linked backlog item(s): `item_057_import_third_party_raw_can_mf4_including_unfinished_recordings`, `item_058_stream_stored_raw_can_frames_to_round_trip_safe_asc_exports`, `item_059_expose_mf4_import_and_raw_asc_download_with_explicit_server_capability`
- Related request(s): `req_033_read_raw_can_mf4_recordings_and_save_traces_as_asc`

# Links
- Request: `req_033_read_raw_can_mf4_recordings_and_save_traces_as_asc`
- Product brief(s): `prod_016_raw_mf4_can_import_and_interoperable_asc_trace_export`
- Architecture decision(s): (none yet)
