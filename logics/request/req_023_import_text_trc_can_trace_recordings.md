## req_023_import_text_trc_can_trace_recordings - Import text TRC CAN trace recordings
> From version: 1.0.0
> Schema version: 1.0
> Status: Draft
> Understanding: 90%
> Confidence: 85%
> Complexity: Medium
> Theme: Trace import interoperability
> Reminder: Update status/understanding/confidence and linked backlog/task references when you edit this doc.

# AI Context
- Summary: Directly import the verified text v1.1 classic-CAN trace layout while preserving the normalized trace pipeline and ASC compatibility.
- Keywords: import, text, trc, can, trace, recordings
- Use when: Planning direct support for text .trc CAN recordings in either product surface.
- Skip when: The input is binary, needs CAN FD/CAN XL payload support, or is an unverified .trc dialect.

# Needs
- Allow operators to import text .trc CAN recordings directly, without a manual conversion to .asc.
- Normalize supported .trc frames into the existing trace, DBC decoding, plotting, reporting, and export workflow.
- Keep unsupported record types and malformed lines visible as import anomalies rather than silently dropping data.

# Context
- The supplied representative recording is CRLF-delimited text, declares $FILEVERSION=1.1, and contains 50,099 classic-CAN Rx frames over roughly 39.2 seconds.
- Each observed data line has a sequence number, a millisecond offset, direction, hexadecimal identifier, DLC, and zero to eight hexadecimal bytes.
- The server importer currently accepts only .asc uploads and routes them to an ASC-specific parser; the local-first PWA likewise exposes only an ASC picker and parser.
- RawCanFrame already represents the fields required for classic CAN data frames, while the current product intentionally preserves CAN FD lines as non-data events.
- This delivery must preserve the current ASC import contract, asynchronous server import behavior, local PWA parity, and file-upload safety limits.
- This functional delivery follows the project release policy: validate locally, commit implementation work, prepare and commit the next SemVer version, push, wait for CI on that exact version-preparation commit, then create and push one annotated version tag and verify the tag-triggered release workflow.

# Acceptance criteria
- AC1: A supported text .trc file can be selected in both the server-backed UI and the local PWA and reaches the existing import workflow without requiring conversion.
- AC2: The supplied v1.1 fixture imports all valid classic CAN data frames with timestamps converted from milliseconds to seconds, preserved Rx/Tx direction, correct hexadecimal IDs, DLCs, and payload bytes.
- AC3: Imported .trc frames decode against selected DBC files and remain available through the existing trace navigation, signals, report, and export APIs exactly as equivalent normalized ASC frames do.
- AC4: Header and comment records are ignored safely; remote requests, warning/error records, unsupported protocol records, malformed fields, payload/DLC mismatches, and DLCs above eight are surfaced as explicit non-data events or import anomalies without corrupting valid frames.
- AC5: ASC behavior remains unchanged, and automated Python, API/UI, and local-PWA tests cover the representative .trc fixture, a compact synthetic edge-case fixture, rejection/diagnostic behavior, and file-picker acceptance.

# Definition of Ready (DoR)
- [x] Problem statement is explicit and user impact is clear.
- [x] Scope boundaries (in/out) are explicit.
- [x] Acceptance criteria are testable.
- [x] Dependencies and known risks are listed.

# Companion docs
- Product brief(s): `prod_010_interoperable_classic_can_trace_import`
- Architecture decision(s): (none yet)

# References
- logics/external/peak.trc
- src/cantracediag/formats/asc.py
- src/cantracediag/pipeline.py
- src/cantracediag/api.py
- src/cantracediag/web/index.html
- spikes/pwa-local-engine/src/asc.ts
- spikes/pwa-local-engine/src/local-backend.ts
- tests/test_asc.py
- tests/test_api.py

# Backlog
- `item_043_add_verified_text_trc_import_with_server_and_local_pwa_parity`
