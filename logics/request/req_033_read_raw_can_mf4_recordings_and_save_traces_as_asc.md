## req_033_read_raw_can_mf4_recordings_and_save_traces_as_asc - Read raw CAN MF4 recordings and save traces as ASC
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Complexity: High
> Theme: Raw CAN trace interoperability
> Reminder: Update status/understanding/confidence and linked backlog/task references when you edit this doc.
> Indicators reviewed: 2026-10-01 15:16:35

# AI Context
The supplied MDF 4.11 recording has stale DT length and zero group cycle counters; source-preserving recovery and independent count verification are required. ASC export operates on stored classic-CAN frames without a DBC, retaining relative time and sparse buses. Server mode is the delivery target; static PWA explicitly rejects these capabilities.

# Needs
- Read raw CAN frames directly from MF4 recordings, including the supplied third-party unfinished MDF 4.11 example.
- Save imported raw CAN traces as ASC for use in other tools without selecting decoded signals or loading a DBC.
- Preserve frame integrity, timestamps, channels and known direction, and make unsupported content and conversion exclusions visible.

# Context
- The server currently supports ASC, text TRC and Vector BLF; MF4 is rejected. RawCanFrame/NonDataEvent isolate import adapters from downstream decoding and DuckDB consumers.
- python-can is already a dependency; asammdf is not installed in the inspected project environment. Evaluate asammdf directly for third-party raw bus logging and safe unfinished-measurement recovery rather than assuming MF4Reader compatibility. Consult https://asammdf.readthedocs.io/en/stable/api.html and https://python-can.readthedocs.io/en/stable/file_io.html; record chosen version, dependency/license constraints and reader limitations before implementation.
- The externally held sample is 2,109,901 bytes, SHA-256 e00a995c1fd4eb47111cad8cd12f7692dd15a176393ef2751e1ec9df5cd03099, has UnFinMF / 4.11 header and unfinished flags 0x25, zero declared CG cycles and a DT length of 24 despite trailing records. See the repo-relative inspection note for structural evidence and its limits.
- A read-only structural scan interpreting the final DT as extending to EOF accounts for 117,797 records: 116,838 CAN1_Rx, 184 CAN1_Rx_IDE and 775 CAN9_Rx. This is a hypothesis to confirm with an independent MDF reader, not an implemented or validated import. Empty FD/LIN/remote/error groups also occur in the schema.
- Current /api/export and report.js require selected decoded signals and emit only CSV/Parquet. Raw ASC needs a format-specific validation branch or separate raw-trace endpoint backed by stored frames, never reconstruction from decoded samples.
- First delivery targets raw classic-CAN data frames in server mode. CAN FD, CAN XL, LIN and signal-only MDF measurements are outside the normalized-frame scope and require explicit diagnostics. Static PWA remains text-only with explicit MF4 rejection.
- Only workflow/scoping documents are created now. No product implementation, dependency installation, release or operational recording is included. Implementation later follows repository validation and release-evidence policy.

# Acceptance criteria
- AC1: Server upload, trusted path import, CLI and server-backed UI accept case-insensitive .mf4/.MF4 filenames alongside ASC/TRC/BLF without changing existing size, security, asynchronous-job and temporary-store safeguards.
- AC2: A project-owned reader imports MDF4 raw classic-CAN data frames without a DBC, including third-party multi-group bus logging: finite relative timestamps in seconds, original numeric bus channels, standard/extended identifiers, exact DLC and payload, and Rx/Tx only when known. No embedded DBC is required or silently selected.
- AC3: The supplied external 00000002.MF4 is successfully read without modifying its bytes. Its unfinalized MDF 4.11 metadata is safely interpreted or finalized only in a disposable copy. An independent reader verifies recovered frame counts and normalized values against the structural baseline in the sample inspection note; zero header cycle counts must never produce a false empty import.
- AC4: Valid frames from multiple groups use deterministic chronological ordering with stable ties based on source record order where recoverable, otherwise documented group/record indices. Timestamps retain the measurement-relative origin, without epoch conversion or rebasing each group. CAN FD/XL, remote/error records, non-CAN buses and malformed records are explicitly diagnosed or counted; unrepairable containers fail without publishing partial state.
- AC5: MF4 imports preserve existing DBC decoding, trace navigation, cursor analysis, plotting, reports and signal exports, with bounded read fragments and store batches, monotonic honest progress and cancellation during initialization as well as record ingestion. Large-input measurements prove that a generator does not hide full-file materialization.
- AC6: An imported trace can be downloaded as a valid Vector-style .asc containing all supported raw classic-CAN data frames without a DBC or selected signals. Export reads stored raw frames, works for MF4 and existing ASC/TRC/BLF sources, and leaves signal CSV/Parquet contracts unchanged.
- AC7: ASC export supports full trace, inclusive A/B range and inclusive visible time range, ignores selected signals and trace display filters, orders by (timestamp_s, seq), retains the original relative time origin and numeric bus identifiers, writes hex identifiers with extended-ID suffix and exact bytes/DLC, and preserves known direction. Missing channel/direction follows an explicit disclosed policy; conversion must not silently invent provenance.
- AC8: Re-importing generated ASC preserves frame count, standard/extended IDs, numeric channels, known direction, DLC and payload exactly, and timestamps within a documented tolerance of at most 1 microsecond for representable values. Diagnostics and non-frame metadata excluded from ASC are disclosed with counts before download and in header comments; unsupported frames are never recoded as classic CAN.
- AC9: Automated generated-fixture parser, pipeline, store, API and UI tests cover multi-group interleaving, equal timestamps, sparse buses, standard/extended frames, DLC 0/8, mixed unsupported types, safe unfinished-file recovery, unrecoverable/truncated files, empty data, ranges, restore, no-DBC/no-signal export, batching, cancellation and ASC/TRC/BLF plus CSV/Parquet regression. The operational sample remains outside git and is checked manually with hash and measured results.
- AC10: Static browser PWA explicitly rejects MF4 with an actionable server-mode message and does not advertise local MF4 or ASC export until implemented separately. Server-backed UI clearly distinguishes raw ASC trace export from selected-signal export, including scopes, empty states, exclusions and correct .asc download naming.

# Definition of Ready (DoR)
- [x] Problem statement is explicit and user impact is clear.
- [x] Scope boundaries (in/out) are explicit.
- [x] Acceptance criteria are testable.
- [x] Dependencies and known risks are listed.

# Companion docs
- Product brief(s): `prod_016_raw_mf4_can_import_and_interoperable_asc_trace_export`
- Architecture decision(s): (none yet)

# References
- README.md
- pyproject.toml
- logics/external/mf4_sample_inspection.md
- src/cantracediag/formats/asc.py
- src/cantracediag/formats/blf.py
- src/cantracediag/models.py
- src/cantracediag/pipeline.py
- src/cantracediag/store.py
- src/cantracediag/export.py
- src/cantracediag/api.py
- src/cantracediag/cli.py
- src/cantracediag/web/index.html
- src/cantracediag/web/js/import.js
- src/cantracediag/web/js/report.js
- spikes/pwa-local-engine/src/local-backend.ts
- tests/test_asc.py
- tests/test_blf.py
- tests/test_blf_integration.py
- tests/test_export.py
- tests/test_api.py

# Backlog
- `item_057_import_third_party_raw_can_mf4_including_unfinished_recordings`
- `item_058_stream_stored_raw_can_frames_to_round_trip_safe_asc_exports`
- `item_059_expose_mf4_import_and_raw_asc_download_with_explicit_server_capability`
