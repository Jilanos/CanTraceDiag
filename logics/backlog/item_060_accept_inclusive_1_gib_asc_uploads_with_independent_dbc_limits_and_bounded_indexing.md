## item_060_accept_inclusive_1_gib_asc_uploads_with_independent_dbc_limits_and_bounded_indexing - Accept inclusive 1 GiB ASC uploads with independent DBC limits and bounded indexing
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: High
> Theme: Large-trace import
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.
> Indicators reviewed: 2026-10-20 09:20:27

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
- request-AC1 -> This backlog slice. Proof: implemented in 54f53f3 (`security.UploadLimits`, `upload.stage_multipart`: inclusive 1,073,741,824 B trace cap, 64 MiB aggregate DBC, 8 MiB envelope, LAN keeps 512 MiB unless overridden, `CANTRACEDIAG_MAX_*_MB` overrides documented in README); `tests/test_upload_limits.py::test_trace_cap_is_inclusive[cap-1|cap|cap+1]`, `test_trace_cap_independent_of_dbc_budget`, `test_default_limits_are_inclusive_1_gib_plus_independent_budgets`, `test_lan_keeps_legacy_aggregate_cap_unless_overridden`; v1.4.0 published exe: exact 1 GiB accepted through the Chrome file picker (407.2 s), 1 GiB + 1 B refused with 413 and an explicit message (docs/qualification-windows-1gib-2026-10-19.md).
- request-AC2 -> This backlog slice. Proof: streamed multipart staging (54f53f3), bounded 50,000-item import batches into an on-disk DuckDB with Arrow columns and a 2 GB buffer cap (e8b6369, 856b484), lazy per-signal decoding streamed in bounded batches and vectorized for plain signals (e8b6369, 0c094f2); `tests/test_asc.py::test_fast_path_matches_general_parser_exactly`, `tests/test_fastdecode.py` (cantools differential + API series identical on both paths); raw ASC export vs source frame by frame on the published exe: 18,728,198 frames (incl. 1,388,464 on channel 9, 4,163,174 extended, 193,076 equal-timestamp lines) 0 mismatches, source SHA-256 unchanged (docs/qualification-windows-1gib-2026-10-19.md).
- request-AC3 -> This backlog slice. Proof: job phases uploading -> loading_dbc -> indexing -> complete with byte-based progress (54f53f3); cancel during transfer (abort + server flag) and indexing, staging removed, reader closed on cancel (75f0f60), ENOSPC -> 507, stale staging pruned at startup; `tests/test_upload_limits.py::test_cancel_during_transfer_stops_streaming`, `test_cancel_flag_before_indexing_aborts_without_replacing`, `test_rejected_upload_removes_staging_and_keeps_previous_analysis`, `test_truncated_body_is_rejected`, `test_insufficient_disk_space_is_actionable`, `test_stale_staging_is_pruned_on_startup`; published exe at 1 GiB: both cancellations 409 with previous analysis kept and no staging left (docs/qualification-windows-1gib-2026-10-19.md).
- request-AC10 -> This backlog slice. Proof: boundary, budget, Content-Length, rollback and fast-path tests listed under AC1-AC3; deterministic generator `scripts/generate_large_asc.py` (multi-channel, extended ids, equal timestamps, malformed records, 15-signal DBC); full 1 GiB qualification of both a local build and the published v1.4.0 exe plus the external 668,097,985 B acquisition (10,613,470 frames, 45 ids, 238.0 s, 0 mismatches), anonymized in docs/qualification-windows-1gib-2026-10-19.md with remaining limits (single reference machine, unsigned, cold first plot 25-39 s, ASC-only guarantee).

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

# Tasks
- `task_049_deliver_standalone_windows_launch_and_one_gib_asc_analysis`

# Notes
- Task `task_049_deliver_standalone_windows_launch_and_one_gib_asc_analysis` was finished via `logics-manager flow finish task` on 2026-10-20.
