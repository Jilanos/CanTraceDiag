## req_031_import_binary_blf_can_trace_recordings - Import binary BLF CAN trace recordings
> From version: 1.0.0
> Schema version: 1.0
> Status: Draft
> Understanding: 90%
> Confidence: 85%
> Complexity: High
> Theme: Binary trace import interoperability
> Reminder: Update status/understanding/confidence and linked backlog/task references when you edit this doc.
> Indicators reviewed: 2026-08-28 10:15:38

# AI Context
- Summary: Define a bounded Vector BLF ingestion contract that keeps binary-recording risks outside the normalized diagnostic pipeline.
- Keywords: import, binary, blf, can, trace, recordings
- Use when: Scoping a server-backed BLF import, its defensive parser boundary, or the PWA capability decision.
- Skip when: Adding MF4, replay, CAN FD/CAN XL, or changing existing ASC/TRC semantics.

# Needs
- Allow operators to select and analyze Vector BLF CAN recordings directly, without conversion to ASC or text TRC.
- Normalize supported BLF classic-CAN data frames into the existing trace, DBC decoding, plotting, reporting, and export workflow.
- Preserve visibility of unsupported BLF objects and malformed binary content through safe, inspectable import diagnostics.

# Context
- The current product imports ASC and verified text TRC only; the API explicitly rejects .blf uploads and both product file pickers exclude the extension.
- The internal RawCanFrame and NonDataEvent models were designed to isolate source formats from DBC decoding, local DuckDB indexing, trace navigation, reports, and exports.
- The Python environment already includes python-can 4.6.1, whose BLF reader can be evaluated behind a project-owned adapter; the static browser PWA cannot use that Python dependency and needs a separate binary-capable strategy.
- Representative trace files can be large and must remain outside the repository. Automated tests must generate a compact deterministic BLF fixture or use a checked-in generator rather than committing operational recordings.
- This delivery must keep existing ASC and TRC behavior, asynchronous server-import progress and cancellation, local upload and path security limits, and the release evidence policy unchanged.

# Acceptance criteria
- AC1: A supported .blf file can be selected in the server-backed UI and accepted by server upload and path-import validation without weakening existing file-size or path-security controls.
- AC2: The supported Vector BLF subset imports classic CAN data frames with correct timestamp conversion, channel, standard or extended identifier, DLC, payload, direction when available, and deterministic ordering into RawCanFrame.
- AC3: Normalized BLF frames decode against selected DBC files and remain available through the existing trace navigation, signals, report, CSV, and Parquet contracts without format-specific consumers.
- AC4: Unsupported BLF object types, CAN FD or CAN XL payloads, remote/error frames, invalid lengths, corrupt containers, and decoder failures are rejected or represented as explicit import diagnostics without corrupting valid frames or leaking partial state.
- AC5: ASC and TRC behavior remain unchanged, and automated parser, pipeline, API/UI, cancellation/progress, and generated-fixture tests prove BLF support and non-regression.
- AC6: The static browser PWA has an explicit, tested BLF capability decision: either it imports the same supported subset locally through a bundled, reviewable binary reader with acceptance and parity coverage, or it clearly rejects BLF before selection while the server-backed import remains available; this decision must not be implicit.

# Definition of Ready (DoR)
- [x] Problem statement is explicit and user impact is clear.
- [x] Scope boundaries (in/out) are explicit.
- [x] Acceptance criteria are testable.
- [x] Dependencies and known risks are listed.

# Companion docs
- Product brief(s): `prod_014_reliable_binary_blf_can_trace_import`
- Architecture decision(s): (none yet)

# References
- README.md
- docs/adr/0002-format-asc-et-cache-local.md
- src/cantracediag/formats/asc.py
- src/cantracediag/formats/trc.py
- src/cantracediag/pipeline.py
- src/cantracediag/api.py
- src/cantracediag/web/index.html
- src/cantracediag/web/js/import.js
- spikes/pwa-local-engine/src/local-backend.ts
- tests/test_api.py

# Backlog
- `item_053_add_bounded_vector_blf_import_with_diagnostics_and_explicit_pwa_capability`
