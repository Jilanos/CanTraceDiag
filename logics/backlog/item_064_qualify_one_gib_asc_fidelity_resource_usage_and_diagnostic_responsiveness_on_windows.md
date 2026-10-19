## item_064_qualify_one_gib_asc_fidelity_resource_usage_and_diagnostic_responsiveness_on_windows - Qualify one GiB ASC fidelity resource usage and diagnostic responsiveness on Windows
> From version: 1.0.0
> Schema version: 1.0
> Status: In progress
> Understanding: 90%
> Confidence: 85%
> Progress: 60%
> Complexity: High
> Theme: Large-file qualification
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.
> Indicators reviewed: 2026-10-19 19:48:19

# AI Context
Existing hot-path budgets use roughly 100,000 rows and do not prove a complete 1 GiB acquisition is usable. Generate repeatable valid ASC inputs at 1 GiB with known frame counts, multi-channel traffic, extended IDs, equal timestamps, mixed DLCs and realistic roughly 45-ID traffic. Include a nontrivial generated DBC with at least 20 messages and eight signals/message; record match coverage and avoid qualifying with an empty DBC or comments-only padding.

# Problem
- Existing hot-path budgets use roughly 100,000 rows and do not prove a complete 1 GiB acquisition is usable.
- A structural scan of the external acquisition is not end-to-end Windows performance evidence.

# Scope
- In:
  - Priority rationale: explicit delivery gate for the central capacity claim; start fixture/baseline work early, qualify the final frozen artifact after other slices.
  - Generate repeatable valid ASC inputs at 1 GiB with known frame counts, multi-channel traffic, extended IDs, equal timestamps, mixed DLCs and realistic roughly 45-ID traffic. Include a nontrivial generated DBC with at least 20 messages and eight signals/message; record match coverage and avoid qualifying with an empty DBC or comments-only padding.
  - Measure the complete picker upload/index-to-ready flow on Windows 11 x64, >=4 cores, 16 GiB RAM, local SSD. Gate at <=15 min, <=6 GiB service-tree and <=2 GiB dedicated-browser peak working set; measure native allocations/process working sets rather than tracemalloc alone. Report cold/warm conditions, disk peak and browser/build identifiers.
  - After import exercise 200-row filtered paging, two signals/4,000-point plots and two-signal A/B cursors with >=20 timed interactions; warm p95 budgets are 2 s/3 s/1 s respectively. Validate full counts/endpoints, selected values and lazy full-resolution results rather than only a screenshot.
  - Measure indexing cancel acknowledgement <=5 s, transfer abort, previous-session preservation, cleanup, retry and restart/restore. Validate file +1 byte rejection and full-size accepted path in the actual executable.
  - Use compact automated fixtures for normal CI and a documented dedicated large qualification job/manual release gate for the full Windows benchmark, storing compact results only. Record baseline before optimizing and repeat only when relevant changes affect results.
  - Re-run the external approximately 637 MiB acquisition with operator-provided DBCs if available, compare 10,613,470 frames/45 IDs/channels 1 and 9 and source hash before/after. It stays external and is supplementary; deterministic 1 GiB proof must not depend on proprietary recordings. Record missing external evidence explicitly.
  - If budgets fail, optimize bounded querying/ingestion within this local scope before claiming support. Any proposed budget relaxation requires an explicit documented scope decision; do not silently relabel a successful import as usable.
- Out:
  - No change to the deployed static PWA import engine or 1 GiB guarantee for non-ASC formats.

# Acceptance criteria
- AC1: The final frozen executable meets the full 1 GiB correctness, <=15 min and 6 GiB/2 GiB memory gates on the documented Windows reference configuration.
- AC2: Recorded interaction p95 and cancellation measurements satisfy the request budgets while values/counts and source bytes remain correct.
- AC3: Synthetic boundary/regression evidence is reproducible without operational files; optional external-recording evidence is anonymized and clearly distinguished from synthetic proof.

# AC Traceability
- request-AC1 -> This backlog slice. Proof: implemented in 54f53f3 (`security.UploadLimits`, `upload.stage_multipart`: inclusive 1,073,741,824 B trace cap, 64 MiB aggregate DBC, 8 MiB envelope, LAN keeps 512 MiB unless overridden, `CANTRACEDIAG_MAX_*_MB` overrides documented in README); `tests/test_upload_limits.py::test_trace_cap_is_inclusive[cap-1|cap|cap+1]`, `test_trace_cap_independent_of_dbc_budget`, `test_default_limits_are_inclusive_1_gib_plus_independent_budgets`, `test_lan_keeps_legacy_aggregate_cap_unless_overridden`; v1.4.0 published exe: exact 1 GiB accepted through the Chrome file picker (407.2 s), 1 GiB + 1 B refused with 413 and an explicit message (docs/qualification-windows-1gib-2026-10-19.md).
- request-AC2 -> This backlog slice. Proof: streamed multipart staging (54f53f3), bounded 50,000-item import batches into an on-disk DuckDB with Arrow columns and a 2 GB buffer cap (e8b6369, 856b484), lazy per-signal decoding streamed in bounded batches and vectorized for plain signals (e8b6369, 0c094f2); `tests/test_asc.py::test_fast_path_matches_general_parser_exactly`, `tests/test_fastdecode.py` (cantools differential + API series identical on both paths); raw ASC export vs source frame by frame on the published exe: 18,728,198 frames (incl. 1,388,464 on channel 9, 4,163,174 extended, 193,076 equal-timestamp lines) 0 mismatches, source SHA-256 unchanged (docs/qualification-windows-1gib-2026-10-19.md).
- request-AC3 -> This backlog slice. Proof: job phases uploading -> loading_dbc -> indexing -> complete with byte-based progress (54f53f3); cancel during transfer (abort + server flag) and indexing, staging removed, reader closed on cancel (75f0f60), ENOSPC -> 507, stale staging pruned at startup; `tests/test_upload_limits.py::test_cancel_during_transfer_stops_streaming`, `test_cancel_flag_before_indexing_aborts_without_replacing`, `test_rejected_upload_removes_staging_and_keeps_previous_analysis`, `test_truncated_body_is_rejected`, `test_insufficient_disk_space_is_actionable`, `test_stale_staging_is_pruned_on_startup`; published exe at 1 GiB: both cancellations 409 with previous analysis kept and no staging left (docs/qualification-windows-1gib-2026-10-19.md).
- request-AC4 -> This backlog slice. Proof: published v1.4.0 exe (SHA-256 9344b2fc...), Windows 11 x64, i7-12700H 14 cores, 16 GiB, NVMe SSD, Chrome 155: import 402.2 s API / 407.2 s UI (limit 900 s); service peak 2,267,430,912 B (limit 6 GiB); browser peak 1,039,253,504 B (limit 2 GiB); warm p95 over 20 interactions: filtered 200-row page 1.456 s API / 0.478 s UI (limit 2 s), two signals <= 4,000 points 0.468 s (limit 3 s), two-signal cursors 0.377 s API / 0.287 s UI (limit 1 s); indexing cancel ack 0.26 s (limit 5 s); fixture counts and DBC density recorded in docs/qualification-windows-1gib-2026-10-19.md.
- request-AC5 -> This backlog slice. Proof: PyInstaller one-file exe from `packaging/windows/CanTraceDiag.spec` with pinned constraints (856b484): Python, FastAPI/Uvicorn, DuckDB, PyArrow, ASC/TRC/BLF/MF4 readers and static UI bundled; loopback-only service opening the default browser (`cantracediag.desktop`); `packaging/windows/smoke.py` 16/16 on the published v1.4.0 exe with a scrubbed environment (no Python on PATH, no PYTHON* variables), on GitHub Actions run 39283800645 and on this Windows 11 machine; README documents Windows 11 x64 as the only guaranteed target.
- request-AC7 -> This backlog slice. Proof: native paths kept on a Windows backend (`normalize_local_path`, `tests/test_paths.py::test_native_windows_keeps_drive_and_unc_paths`); per-user `%LOCALAPPDATA%\CanTraceDiag` data/logs/instance; second launch attaches, other version refused, occupied/excluded ports skipped by bound-socket fallback, `--stop` and console close stop the service (`tests/test_desktop.py`); smoke 16/16 covers non-ASCII and spaced paths, occupied port, attach, stop and restart restore; launcher test passes from a `\\wsl.localhost` checkout; external acquisition read in place from a `\\wsl.localhost` share.
- request-AC8 -> This backlog slice. Proof: existing local UI unchanged and its Playwright suite green (344 pytest incl. E2E); packaged smoke imports ASC+DBC, TRC, BLF and raw-CAN MF4 (chardet mypyc modules bundled for asammdf), plots, trace paging, cursors, report, CSV and raw ASC export, restore; README states the 1 GiB guarantee is ASC-only; PWA untouched: 86 node tests, build and browser smoke `ok: true`, release deploy job green and https://cantracediag.paulmondou.fr/ 200 after v1.4.0.
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
- Rationale: explicit delivery gate for the central capacity claim; start fixture/baseline work early, qualify the final frozen artifact after other slices.
