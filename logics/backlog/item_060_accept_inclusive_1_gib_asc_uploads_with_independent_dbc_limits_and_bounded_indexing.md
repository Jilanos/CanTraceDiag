## item_060_accept_inclusive_1_gib_asc_uploads_with_independent_dbc_limits_and_bounded_indexing - Accept inclusive 1 GiB ASC uploads with independent DBC limits and bounded indexing
> From version: 1.0.0
> Schema version: 1.0
> Status: In progress
> Understanding: 90%
> Confidence: 85%
> Progress: 60%
> Complexity: High
> Theme: Large-trace import
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.
> Indicators reviewed: 2026-10-19 11:48:16

# AI Context
The aggregate 512 MiB cap blocks large acquisitions; a simple 1 GiB cap still rejects boundary-sized traces with DBCs. Separate trace, aggregate DBC and transport-envelope limits. Define local-app defaults at 1 GiB/64 MiB/8 MiB and explicit override precedence; preserve established deployments or provide documented configuration migration. Count actual streamed bytes regardless of Content-Length; validate selected library DBC policy explicitly.

# Problem
- The aggregate 512 MiB cap blocks large acquisitions; a simple 1 GiB cap still rejects boundary-sized traces with DBCs.
- Upload middleware/multipart spooling, indexing and failure cleanup must all honor the actual large-file contract.

# Scope
- In:
  - Priority rationale: prerequisite for every large-file validation and the desktop promise.
  - Separate trace, aggregate DBC and transport-envelope limits. Define local-app defaults at 1 GiB/64 MiB/8 MiB and explicit override precedence; preserve established deployments or provide documented configuration migration. Count actual streamed bytes regardless of Content-Length; validate selected library DBC policy explicitly.
  - Audit framework multipart spooling and upload transfer before endpoint execution, worker/index batches, lazy decoding and temporary copies; maintain bounded memory and disk-backed analysis. Apply independent trace cap to trusted path imports too, with platform-aware path handling in the desktop slice.
  - Reject oversized data early where possible; stream-enforce missing/false lengths. Do not inflate the 1 GiB trace limit to absorb overhead. Check free space conservatively across upload/index/temp locations, bound application staging use and handle ENOSPC mid-operation safely.
  - Keep the previous successful analysis until atomic completion. Poll cancellation through indexing and make browser transfer abort remove staged uploads; track upload versus indexing progress without displaying completed state before readiness.
  - Add focused boundary/spooling tests using valid ASC plus legal header/comment padding to hit exact byte counts, stream counters for cheap edge checks and at least one real full-size qualification. Do not substitute a mocked-size tiny input for the full 1 GiB proof.
- Out:
  - No change to the deployed static PWA import engine or 1 GiB guarantee for non-ASC formats.

# Acceptance criteria
- AC1: A 1 GiB ASC with permitted DBC uploads passes the real picker/API path; trace plus one byte and independent DBC/envelope overages fail with clear errors, including absent/false lengths.
- AC2: Batched disk-backed ingestion preserves normalized frame values and ordering without eager full-trace samples, and cancellation/failure leaves no published partial analysis or orphan staging files.
- AC3: Size, transport, malformed-record, space-exhaustion and rollback evidence is recorded for synthetic fixtures.

# AC Traceability
- request-AC1 -> This backlog slice. Proof deferred to implementation closeout. Required evidence for request-AC1: The Windows local application accepts a classic-CAN ASC trace of exactly 1,073,741,824 bytes through the normal browser file picker, with an independent 64 MiB aggregate uploaded-DBC budget and 8 MiB multipart-envelope allowance. The trace cap is inclusive and applies independently of DBCs; 1 GiB plus one byte is rejected clearly. Defaults need no environment-variable edit. Document the limits and preserve explicit administrator overrides without silently weakening existing server/LAN deployments.
- request-AC2 -> This backlog slice. Proof deferred to implementation closeout. Required evidence for request-AC2: Upload spooling, ASC parsing, indexing and decoding avoid whole-file text/byte buffers and eager full-trace signal materialization; use bounded batches, disk-backed indexes and bounded browser responses. Original timestamps, source ordering for ties, channels including sparse channel 9, standard/extended IDs, direction, DLC and payload remain exact. No source mutation, downsampling at ingestion or silent frame dropping is allowed.
- request-AC3 -> This backlog slice. Proof deferred to implementation closeout. Required evidence for request-AC3: Upload, indexing and ready phases remain distinguishable with honest progress. Cancellation works during transfer and indexing, preserves the previously loaded analysis, removes staging data and never publishes a partial replacement. Size errors, corrupt input, insufficient space and interrupted work produce actionable errors and recoverable state.
- request-AC10 -> This backlog slice. Proof deferred to implementation closeout. Required evidence for request-AC10: Boundary tests cover trace cap minus one/exact/plus one byte, separate DBC/envelope budgets, missing or misleading Content-Length and streaming enforcement. Generated fixtures cover multi-channel/extended IDs, equal timestamps, malformed records, cancellation/rollback and meaningful DBC decoding. Run a full 1 GiB Windows qualification plus the external roughly 637 MiB acquisition when available; publish only anonymized counts, hashes and timing/memory results, never operational traces, payloads, DBC contents or machine-specific paths. Closeout maps every criterion to evidence and records remaining platform limits.

# Decision framing
- Product framing: Not needed
- Architecture framing: Not needed

# Links
- Product brief(s): `prod_017_portable_windows_local_workstation_for_1_gib_asc_acquisitions`
- Architecture decision(s): (none yet)
- Request: `req_034_deliver_a_standalone_windows_local_application_for_asc_traces_up_to_1_gib`
- Primary task(s): `task_049_deliver_standalone_windows_launch_and_one_gib_asc_analysis`

# Priority
- Priority: High
- Rationale: prerequisite for every large-file validation and the desktop promise.
