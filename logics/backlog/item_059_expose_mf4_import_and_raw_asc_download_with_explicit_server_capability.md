## item_059_expose_mf4_import_and_raw_asc_download_with_explicit_server_capability - Expose MF4 import and raw ASC download with explicit server capability
> From version: 1.0.0
> Schema version: 1.0
> Status: Ready
> Understanding: 90%
> Confidence: 85%
> Progress: 0%
> Complexity: Medium
> Theme: Trace conversion UX and validation
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.
> Indicators reviewed: 2026-10-01 14:28:02

# AI Context
Depends on the MF4 adapter and raw ASC export contract. report.js currently blocks export when no signals are selected and names downloads CSV/Parquet; adapt validation and filenames only for raw ASC. Static PWA needs explicit capability rejection, and conversion warnings must be visible before download.

# Problem
- File pickers reject MF4 and the export dialog blocks operations when no decoded signal is selected.
- Static PWA must not advertise Python-only functionality, and users need visible conversion scope and exclusions.

# Scope
- In:
  - Accept .mf4/.MF4 in server mode and update supported-format help, CLI documentation and import copy consistently.
  - Offer raw trace ASC in the export flow, including full/A-B/visible scopes, without requiring DBC or signals; keep signal CSV/Parquet validations and filenames correct.
  - Show recovery notices, skipped-record counts, unavailable provenance and export exclusions before conversion; ignore display filters for raw export and explain its time-only scope.
  - Explicitly reject MF4 in static PWA and expose server-only ASC export as unavailable there; test capability routing so users cannot trigger misleading local actions.
  - Add API/UI acceptance coverage and document a manual external-sample import -> ASC download -> ASC re-import check with hash, counts, channels, timestamp ranges and payload/ID comparison.
  - Update README/support matrix, validation commands and Logics closeout evidence. Follow implementation/release policy only during later authorized delivery.
- Out:
  - A browser MDF decoder, browser ASC writer, new desktop integrations or implementation during this corpus creation.

# Acceptance criteria
- AC1: Server upload, trusted path import, CLI and server-backed UI accept case-insensitive .mf4/.MF4 filenames alongside ASC/TRC/BLF without changing existing size, security, asynchronous-job and temporary-store safeguards.
- AC6: An imported trace can be downloaded as a valid Vector-style .asc containing all supported raw classic-CAN data frames without a DBC or selected signals. Export reads stored raw frames, works for MF4 and existing ASC/TRC/BLF sources, and leaves signal CSV/Parquet contracts unchanged.
- AC7: ASC export supports full trace, inclusive A/B range and inclusive visible time range, ignores selected signals and trace display filters, orders by (timestamp_s, seq), retains the original relative time origin and numeric bus identifiers, writes hex identifiers with extended-ID suffix and exact bytes/DLC, and preserves known direction. Missing channel/direction follows an explicit disclosed policy; conversion must not silently invent provenance.
- AC8: Re-importing generated ASC preserves frame count, standard/extended IDs, numeric channels, known direction, DLC and payload exactly, and timestamps within a documented tolerance of at most 1 microsecond for representable values. Diagnostics and non-frame metadata excluded from ASC are disclosed with counts before download and in header comments; unsupported frames are never recoded as classic CAN.
- AC9: Automated generated-fixture parser, pipeline, store, API and UI tests cover multi-group interleaving, equal timestamps, sparse buses, standard/extended frames, DLC 0/8, mixed unsupported types, safe unfinished-file recovery, unrecoverable/truncated files, empty data, ranges, restore, no-DBC/no-signal export, batching, cancellation and ASC/TRC/BLF plus CSV/Parquet regression. The operational sample remains outside git and is checked manually with hash and measured results.
- AC10: Static browser PWA explicitly rejects MF4 with an actionable server-mode message and does not advertise local MF4 or ASC export until implemented separately. Server-backed UI clearly distinguishes raw ASC trace export from selected-signal export, including scopes, empty states, exclusions and correct .asc download naming.

# AC Traceability
- request-AC1 -> This backlog slice. Proof: AC1: Server upload, trusted path import, CLI and server-backed UI accept case-insensitive .mf4/.MF4 filenames alongside ASC/TRC/BLF without changing existing size, security, asynchronous-job and temporary-store safeguards.
- request-AC6 -> This backlog slice. Proof: AC6: An imported trace can be downloaded as a valid Vector-style .asc containing all supported raw classic-CAN data frames without a DBC or selected signals. Export reads stored raw frames, works for MF4 and existing ASC/TRC/BLF sources, and leaves signal CSV/Parquet contracts unchanged.
- request-AC7 -> This backlog slice. Proof: AC7: ASC export supports full trace, inclusive A/B range and inclusive visible time range, ignores selected signals and trace display filters, orders by (timestamp_s, seq), retains the original relative time origin and numeric bus identifiers, writes hex identifiers with extended-ID suffix and exact bytes/DLC, and preserves known direction. Missing channel/direction follows an explicit disclosed policy; conversion must not silently invent provenance.
- request-AC8 -> This backlog slice. Proof: AC8: Re-importing generated ASC preserves frame count, standard/extended IDs, numeric channels, known direction, DLC and payload exactly, and timestamps within a documented tolerance of at most 1 microsecond for representable values. Diagnostics and non-frame metadata excluded from ASC are disclosed with counts before download and in header comments; unsupported frames are never recoded as classic CAN.
- request-AC9 -> This backlog slice. Proof: AC9: Automated generated-fixture parser, pipeline, store, API and UI tests cover multi-group interleaving, equal timestamps, sparse buses, standard/extended frames, DLC 0/8, mixed unsupported types, safe unfinished-file recovery, unrecoverable/truncated files, empty data, ranges, restore, no-DBC/no-signal export, batching, cancellation and ASC/TRC/BLF plus CSV/Parquet regression. The operational sample remains outside git and is checked manually with hash and measured results.
- request-AC10 -> This backlog slice. Proof: AC10: Static browser PWA explicitly rejects MF4 with an actionable server-mode message and does not advertise local MF4 or ASC export until implemented separately. Server-backed UI clearly distinguishes raw ASC trace export from selected-signal export, including scopes, empty states, exclusions and correct .asc download naming.

# Decision framing
- Product framing: Not needed
- Architecture framing: Not needed

# Links
- Product brief(s): `prod_016_raw_mf4_can_import_and_interoperable_asc_trace_export`
- Architecture decision(s): (none yet)
- Request: `req_033_read_raw_can_mf4_recordings_and_save_traces_as_asc`
- Primary task(s): `task_048_deliver_raw_can_mf4_import_and_asc_trace_export`

# Priority
- Priority: High - completes the usable user flow after the import and serialization prerequisites.
- Rationale: Makes the two backend capabilities usable and keeps server/PWA support truthful.
