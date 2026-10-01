## item_057_import_third_party_raw_can_mf4_including_unfinished_recordings - Import third-party raw CAN MF4 including unfinished recordings
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: High
> Theme: MDF4 raw bus logging
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.
> Indicators reviewed: 2026-10-01 15:16:36

# AI Context
Start with logics/external/mf4_sample_inspection.md and verify its provisional 117,797-record baseline with an independent MDF reader. Test sample-like unfinished metadata synthetically. Preserve direction and bus IDs before using the ASC exporter; initialization must remain cancellable and memory usage measured.

# Problem
- The existing format dispatch rejects MF4, and unfinished metadata can make a real recording appear empty.
- Generic library iterators may drop direction or unsupported objects, reorder groups incorrectly, or load the whole file.

# Scope
- In:
  - Characterize sample schema and independently confirm recovered counts/values without source mutation; document supported MDF versions/layouts and unfinished flags.
  - Choose and pin/test a compatible raw-reader dependency strategy; add a project-owned streaming adapter, lazy imports and actionable missing-dependency errors if optional. Do not create a bespoke full MDF implementation.
  - Normalize classic-CAN frames, merge groups deterministically, preserve relative time, bus and known direction, and validate ID/DLC/DataLength/payload consistently with existing readers.
  - Recover the supplied unfinished layout in memory or a disposable copy; verify structural integrity before publishing a session; expose recovered-state warning and diagnostics/counts for skipped content.
  - Route MF4 through server API and CLI with temporary-store rollback, progress/cancellation and bounded fragments; keep existing downstream consumers source-agnostic.
  - Generate compact finalized and unfinished mixed-group fixtures, including a sample-like stale DT length/zero-cycle layout; measure representative large-recording memory/cancellation and test decode/restore/non-regression.
- Out:
  - MF4 writing, original-file finalization, predecoded-only signals, CAN FD/XL and non-CAN normalization.
  - Committing the operational sample or requiring it in CI.

# Acceptance criteria
- AC1: Server upload, trusted path import, CLI and server-backed UI accept case-insensitive .mf4/.MF4 filenames alongside ASC/TRC/BLF without changing existing size, security, asynchronous-job and temporary-store safeguards.
- AC2: A project-owned reader imports MDF4 raw classic-CAN data frames without a DBC, including third-party multi-group bus logging: finite relative timestamps in seconds, original numeric bus channels, standard/extended identifiers, exact DLC and payload, and Rx/Tx only when known. No embedded DBC is required or silently selected.
- AC3: The supplied external 00000002.MF4 is successfully read without modifying its bytes. Its unfinalized MDF 4.11 metadata is safely interpreted or finalized only in a disposable copy. An independent reader verifies recovered frame counts and normalized values against the structural baseline in the sample inspection note; zero header cycle counts must never produce a false empty import.
- AC4: Valid frames from multiple groups use deterministic chronological ordering with stable ties based on source record order where recoverable, otherwise documented group/record indices. Timestamps retain the measurement-relative origin, without epoch conversion or rebasing each group. CAN FD/XL, remote/error records, non-CAN buses and malformed records are explicitly diagnosed or counted; unrepairable containers fail without publishing partial state.
- AC5: MF4 imports preserve existing DBC decoding, trace navigation, cursor analysis, plotting, reports and signal exports, with bounded read fragments and store batches, monotonic honest progress and cancellation during initialization as well as record ingestion. Large-input measurements prove that a generator does not hide full-file materialization.
- AC9: Automated generated-fixture parser, pipeline, store, API and UI tests cover multi-group interleaving, equal timestamps, sparse buses, standard/extended frames, DLC 0/8, mixed unsupported types, safe unfinished-file recovery, unrecoverable/truncated files, empty data, ranges, restore, no-DBC/no-signal export, batching, cancellation and ASC/TRC/BLF plus CSV/Parquet regression. The operational sample remains outside git and is checked manually with hash and measured results.

# AC Traceability
- request-AC1 -> This backlog slice. Proof: AC1: Server upload, trusted path import, CLI and server-backed UI accept case-insensitive .mf4/.MF4 filenames alongside ASC/TRC/BLF without changing existing size, security, asynchronous-job and temporary-store safeguards.
- request-AC2 -> This backlog slice. Proof: AC2: A project-owned reader imports MDF4 raw classic-CAN data frames without a DBC, including third-party multi-group bus logging: finite relative timestamps in seconds, original numeric bus channels, standard/extended identifiers, exact DLC and payload, and Rx/Tx only when known. No embedded DBC is required or silently selected.
- request-AC3 -> This backlog slice. Proof: AC3: The supplied external 00000002.MF4 is successfully read without modifying its bytes. Its unfinalized MDF 4.11 metadata is safely interpreted or finalized only in a disposable copy. An independent reader verifies recovered frame counts and normalized values against the structural baseline in the sample inspection note; zero header cycle counts must never produce a false empty import.
- request-AC4 -> This backlog slice. Proof: AC4: Valid frames from multiple groups use deterministic chronological ordering with stable ties based on source record order where recoverable, otherwise documented group/record indices. Timestamps retain the measurement-relative origin, without epoch conversion or rebasing each group. CAN FD/XL, remote/error records, non-CAN buses and malformed records are explicitly diagnosed or counted; unrepairable containers fail without publishing partial state.
- request-AC5 -> This backlog slice. Proof: AC5: MF4 imports preserve existing DBC decoding, trace navigation, cursor analysis, plotting, reports and signal exports, with bounded read fragments and store batches, monotonic honest progress and cancellation during initialization as well as record ingestion. Large-input measurements prove that a generator does not hide full-file materialization.
- request-AC9 -> This backlog slice. Proof: AC9: Automated generated-fixture parser, pipeline, store, API and UI tests cover multi-group interleaving, equal timestamps, sparse buses, standard/extended frames, DLC 0/8, mixed unsupported types, safe unfinished-file recovery, unrecoverable/truncated files, empty data, ranges, restore, no-DBC/no-signal export, batching, cancellation and ASC/TRC/BLF plus CSV/Parquet regression. The operational sample remains outside git and is checked manually with hash and measured results.

# Decision framing
- Product framing: Not needed
- Architecture framing: Not needed

# Links
- Product brief(s): `prod_016_raw_mf4_can_import_and_interoperable_asc_trace_export`
- Architecture decision(s): (none yet)
- Request: `req_033_read_raw_can_mf4_recordings_and_save_traces_as_asc`
- Primary task(s): `task_048_deliver_raw_can_mf4_import_and_asc_trace_export`

# Priority
- Priority: High - prerequisite for analyzing the supplied recording and validating conversion end to end.
- Rationale: Prerequisite for the supplied MF4 recording and its end-to-end conversion.

# Tasks
- `task_048_deliver_raw_can_mf4_import_and_asc_trace_export`

# Notes
- Task `task_048_deliver_raw_can_mf4_import_and_asc_trace_export` was finished via `logics-manager flow finish task` on 2026-10-01.
