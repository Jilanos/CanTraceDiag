## item_043_add_verified_text_trc_import_with_server_and_local_pwa_parity - Add verified text TRC import with server and local-PWA parity
> From version: 1.0.0
> Schema version: 1.0
> Status: Ready
> Understanding: 90%
> Confidence: 85%
> Progress: 0%
> Complexity: Medium
> Theme: Trace import interoperability
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# AI Context
- Summary: Add one verified .trc grammar and route it through the existing server and browser-local import contracts without duplicating consumers.
- Keywords: add, verified, text, trc, import, server, local, pwa, parity
- Use when: Implementing or testing parser, picker, API, and local-PWA parity for text .trc files.
- Skip when: Broadening support to binary recordings, additional dialects, or CAN FD/CAN XL.

# Problem
- Operators cannot analyze supported .trc recordings directly because both import surfaces restrict traces to .asc.
- A format-specific parser is needed to convert millisecond offsets and text record fields into the existing normalized frame/event model without weakening integrity checks.

# Scope
- In:
  - Add a streaming Python parser for the verified text .trc v1.1 classic-CAN layout and route trace import by extension without changing the normalized pipeline.
  - Add a matching local-PWA parser and format dispatch so the browser-only workflow accepts the same supported input.
  - Update upload validation, file-picker labels and accept attributes, CLI/help copy where needed, and user-facing import diagnostics for .trc.
  - Add a minimal checked-in .trc fixture derived from the supplied recording plus focused malformed, remote-request, warning/error, unsupported-record, extended-ID, zero-DLC, and payload/DLC mismatch coverage.
  - Verify frame count, timestamp conversion, direction, identifiers, payloads, DBC decoding, reporting, exports, cancellation/progress behavior, and ASC non-regression across server and local-PWA paths.
  - Record the implementation commit SHA, CI run, annotated tag, and release outcome in the task closeout; never force-push or retag a release.
- Out:
  - CAN FD and CAN XL ingestion or decoding.
  - Binary trace reader support or automatic conversion by external tools.
  - Unverified .trc dialects beyond the documented v1.1 classic-CAN layout, except for safe diagnostic rejection.

# Acceptance criteria
- AC1: Both trace pickers accept .asc and .trc; the server upload and path-import endpoints accept supported .trc names without weakening file-size and path security controls.
- AC2: The supplied-recording-derived fixture produces the expected normalized frame count and representative first, middle, and final frame values, including millisecond-to-second timestamps and Rx direction.
- AC3: Valid .trc frames work with the existing DBC decode, trace navigation, report, CSV, and Parquet contracts without a format-specific consumer path.
- AC4: Invalid or unsupported .trc records are accounted for as safe, inspectable events/anomalies and never produce malformed RawCanFrame data.
- AC5: Python unit tests, API/UI tests, and local-PWA tests demonstrate TRC support and demonstrate that the ASC suite retains its current behavior.

# AC Traceability
- request-AC1 -> This backlog slice. Proof: AC1: Both trace pickers accept .asc and .trc; the server upload and path-import endpoints accept supported .trc names without weakening file-size and path security controls.
- request-AC2 -> This backlog slice. Proof: AC2: The supplied-recording-derived fixture produces the expected normalized frame count and representative first, middle, and final frame values, including millisecond-to-second timestamps and Rx direction.
- request-AC3 -> This backlog slice. Proof: AC3: Valid .trc frames work with the existing DBC decode, trace navigation, report, CSV, and Parquet contracts without a format-specific consumer path.
- request-AC4 -> This backlog slice. Proof: AC4: Invalid or unsupported .trc records are accounted for as safe, inspectable events/anomalies and never produce malformed RawCanFrame data.
- request-AC5 -> This backlog slice. Proof: AC5: Python unit tests, API/UI tests, and local-PWA tests demonstrate TRC support and demonstrate that the ASC suite retains its current behavior.

# Decision framing
- Product framing: Not needed
- Architecture framing: Not needed

# Links
- Product brief(s): `prod_010_interoperable_classic_can_trace_import`
- Architecture decision(s): (none yet)
- Request: `req_023_import_text_trc_can_trace_recordings`
- Primary task(s): `task_042_deliver_verified_text_trc_trace_import`

# Priority
- Priority: High
- Rationale: Set by scaffold input or defaulted for grooming.
