## item_053_add_bounded_vector_blf_import_with_diagnostics_and_explicit_pwa_capability - Add bounded Vector BLF import with diagnostics and explicit PWA capability
> From version: 1.0.0
> Schema version: 1.0
> Status: Ready
> Understanding: 90%
> Confidence: 85%
> Progress: 0%
> Complexity: High
> Theme: Binary trace import interoperability
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.
> Indicators reviewed: 2026-08-28 10:15:38

# AI Context
- Summary: Build one defensive binary-format adapter and expose its explicitly tested support boundary consistently across product surfaces.
- Keywords: add, bounded, vector, blf, import, diagnostics, explicit, pwa, capability
- Use when: Implementing BLF parser dispatch, safety diagnostics, server import integration, or the PWA BLF decision.
- Skip when: Implementing unrelated binary formats, bus protocols, or downstream DBC/report changes.

# Problem
- Operators must convert BLF recordings before analysis, which adds friction and can weaken provenance.
- Binary object streams need a bounded, defensive adapter so malformed or unsupported records cannot contaminate the normalized trace pipeline.
- The browser-local PWA currently parses text only, so its BLF boundary must be implemented or explicitly constrained before its picker claims support.

# Scope
- In:
  - Define and document the supported Vector BLF classic-CAN object subset, timestamp origin and conversion, channel mapping, direction semantics, ordering rules, and diagnostic taxonomy.
  - Add a streaming Python BLF adapter behind the existing format-dispatch boundary, evaluating the installed python-can reader and wrapping its exceptions, unsupported objects, and metadata into safe project-owned behavior.
  - Route .blf through server upload, path import, CLI/help copy, and the server-backed UI picker while retaining size, suffix, path, progress, cancellation, and temporary-store safeguards.
  - Ensure BLF frames pass through the current DBC decoder, DuckDB store, trace, report, CSV, and Parquet paths with no BLF-specific consumer branch.
  - Generate deterministic compact BLF test data from source code and add focused coverage for standard and extended frames, multiple channels, ordering, timestamps, zero DLC, unsupported objects, corruption, cancellation, progress, API/UI import, ASC/TRC non-regression, and representative large-input batching.
  - Decide and record the static-PWA BLF boundary: implement a bundled local binary reader with equivalent supported-subset tests if feasible within bundle and memory constraints, otherwise reject .blf explicitly in the PWA picker and product copy while preserving its ASC/TRC support.
  - Record implementation, CI, release-tag, and release-workflow evidence at task closeout according to the project release policy.
- Out:
  - MF4 and other binary trace formats.
  - CAN FD, CAN XL, LIN, FlexRay, and replay support.
  - Committing operational BLF recordings or broadening file-upload size and security limits.

# Acceptance criteria
- AC1: Server-backed trace selection, upload, and trusted path import accept .blf alongside .asc and .trc while retaining current rejection behavior for unsupported names and unsafe paths.
- AC2: A generated deterministic BLF fixture proves correct normalized values for ordered standard and extended classic-CAN frames, timestamps, channels, DLCs, payloads, and direction metadata when present.
- AC3: BLF-derived normalized frames exercise existing DBC decode, trace navigation, report, CSV, and Parquet behavior without a format-specific downstream implementation.
- AC4: Unsupported or unsafe BLF content produces clear diagnostics or a safe import failure, never malformed RawCanFrame values, a hung job, or a partially published trace.
- AC5: Parser, pipeline, API/UI, progress/cancellation, generated-fixture, and ASC/TRC regression tests pass in the documented local validation commands.
- AC6: Browser-local PWA behavior for .blf is covered by automated tests and matches the recorded capability decision: local supported-subset import or deliberate pre-selection rejection.

# AC Traceability
- request-AC1 -> This backlog slice. Proof: AC1: Server-backed trace selection, upload, and trusted path import accept .blf alongside .asc and .trc while retaining current rejection behavior for unsupported names and unsafe paths.
- request-AC2 -> This backlog slice. Proof: AC2: A generated deterministic BLF fixture proves correct normalized values for ordered standard and extended classic-CAN frames, timestamps, channels, DLCs, payloads, and direction metadata when present.
- request-AC3 -> This backlog slice. Proof: AC3: BLF-derived normalized frames exercise existing DBC decode, trace navigation, report, CSV, and Parquet behavior without a format-specific downstream implementation.
- request-AC4 -> This backlog slice. Proof: AC4: Unsupported or unsafe BLF content produces clear diagnostics or a safe import failure, never malformed RawCanFrame values, a hung job, or a partially published trace.
- request-AC5 -> This backlog slice. Proof: AC5: Parser, pipeline, API/UI, progress/cancellation, generated-fixture, and ASC/TRC regression tests pass in the documented local validation commands.
- request-AC6 -> This backlog slice. Proof: AC6: Browser-local PWA behavior for .blf is covered by automated tests and matches the recorded capability decision: local supported-subset import or deliberate pre-selection rejection.

# Decision framing
- Product framing: Not needed
- Architecture framing: Not needed

# Links
- Product brief(s): `prod_014_reliable_binary_blf_can_trace_import`
- Architecture decision(s): (none yet)
- Request: `req_031_import_binary_blf_can_trace_recordings`
- Primary task(s): `task_046_deliver_reliable_binary_blf_trace_import`

# Priority
- Priority: High
- Rationale: Set by scaffold input or defaulted for grooming.
