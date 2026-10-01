## item_058_stream_stored_raw_can_frames_to_round_trip_safe_asc_exports - Stream stored raw CAN frames to round-trip-safe ASC exports
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: High
> Theme: Raw trace ASC serialization
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.
> Indicators reviewed: 2026-10-01 15:16:36

# AI Context
Use raw frames and global seq from DuckDB, not decoded signal samples. Export every supported frame within the chosen inclusive time range, retaining relative timestamps and sparse numeric channels. Prove ASC-reader round trips without a DBC or signal selection and block undisclosed channel/direction invention.

# Problem
- Existing exports operate on selected decoded signals, so they cannot save a raw CAN recording without a DBC.
- ASC conversion needs explicit timestamp precision, channel/direction policies and exclusion visibility to avoid silent information loss.

# Scope
- In:
  - Add a bounded store iterator over raw frames ordered by (timestamp_s, seq), with full or inclusive time-range selection and no decoded-signal/display-filter dependency.
  - Define an ASC serialization contract compatible with the project ASC reader and Vector-style syntax: base hex timestamps absolute for retained relative timestamps, deterministic header/comments, numeric channel, extended-ID suffix, Rx/Tx, data-frame marker, DLC and hex payload.
  - Use at least six fractional digits and prove <=1 microsecond timestamp round-trip error; preserve sparse original numeric channels without renumbering. Validate unsupported/nonfinite values.
  - Define unknown channel/direction policy before implementation: default safely block affected conversion with clear explanation rather than inventing metadata; any explicit fallback must be disclosed and tested. Known-value sample conversion remains lossless.
  - Expose raw ASC download through a dedicated endpoint or a scoped existing-endpoint extension with signal validation only for CSV/Parquet; preserve auth, scope checks, range handling and session-lifetime cleanup.
  - Stream server output with bounded memory and valid content disposition/media type. Disclose excluded event counts/recovery warnings in metadata/UI before download and ASC comments. Empty ranges produce a valid header-only ASC and an explicit empty result.
  - Add ASC reader round-trip and API regression tests for standard/extended IDs, equal times, buses 1/9, DLC 0/8, scopes, no-DBC/no-signal, restored sessions and excluded diagnostics.
- Out:
  - Signal-to-frame reconstruction, MF4 output, arbitrary metadata preservation and exporting unsupported events as data frames.
  - ASC byte-for-byte recreation of a source file or changing CSV/Parquet signal contracts.

# Acceptance criteria
- AC6: An imported trace can be downloaded as a valid Vector-style .asc containing all supported raw classic-CAN data frames without a DBC or selected signals. Export reads stored raw frames, works for MF4 and existing ASC/TRC/BLF sources, and leaves signal CSV/Parquet contracts unchanged.
- AC7: ASC export supports full trace, inclusive A/B range and inclusive visible time range, ignores selected signals and trace display filters, orders by (timestamp_s, seq), retains the original relative time origin and numeric bus identifiers, writes hex identifiers with extended-ID suffix and exact bytes/DLC, and preserves known direction. Missing channel/direction follows an explicit disclosed policy; conversion must not silently invent provenance.
- AC8: Re-importing generated ASC preserves frame count, standard/extended IDs, numeric channels, known direction, DLC and payload exactly, and timestamps within a documented tolerance of at most 1 microsecond for representable values. Diagnostics and non-frame metadata excluded from ASC are disclosed with counts before download and in header comments; unsupported frames are never recoded as classic CAN.
- AC9: Automated generated-fixture parser, pipeline, store, API and UI tests cover multi-group interleaving, equal timestamps, sparse buses, standard/extended frames, DLC 0/8, mixed unsupported types, safe unfinished-file recovery, unrecoverable/truncated files, empty data, ranges, restore, no-DBC/no-signal export, batching, cancellation and ASC/TRC/BLF plus CSV/Parquet regression. The operational sample remains outside git and is checked manually with hash and measured results.

# AC Traceability
- request-AC6 -> This backlog slice. Proof: AC6: An imported trace can be downloaded as a valid Vector-style .asc containing all supported raw classic-CAN data frames without a DBC or selected signals. Export reads stored raw frames, works for MF4 and existing ASC/TRC/BLF sources, and leaves signal CSV/Parquet contracts unchanged.
- request-AC7 -> This backlog slice. Proof: AC7: ASC export supports full trace, inclusive A/B range and inclusive visible time range, ignores selected signals and trace display filters, orders by (timestamp_s, seq), retains the original relative time origin and numeric bus identifiers, writes hex identifiers with extended-ID suffix and exact bytes/DLC, and preserves known direction. Missing channel/direction follows an explicit disclosed policy; conversion must not silently invent provenance.
- request-AC8 -> This backlog slice. Proof: AC8: Re-importing generated ASC preserves frame count, standard/extended IDs, numeric channels, known direction, DLC and payload exactly, and timestamps within a documented tolerance of at most 1 microsecond for representable values. Diagnostics and non-frame metadata excluded from ASC are disclosed with counts before download and in header comments; unsupported frames are never recoded as classic CAN.
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
- Priority: High - directly delivers the requested save-as-ASC capability and can use existing normalized traces.
- Rationale: Directly provides the requested save-as-ASC behavior using existing normalized traces.

# Tasks
- `task_048_deliver_raw_can_mf4_import_and_asc_trace_export`

# Notes
- Task `task_048_deliver_raw_can_mf4_import_and_asc_trace_export` was finished via `logics-manager flow finish task` on 2026-10-01.
