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
> Indicators reviewed: 2026-10-19 11:48:16

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
- request-AC1 -> This backlog slice. Proof deferred to implementation closeout. Required evidence for request-AC1: The Windows local application accepts a classic-CAN ASC trace of exactly 1,073,741,824 bytes through the normal browser file picker, with an independent 64 MiB aggregate uploaded-DBC budget and 8 MiB multipart-envelope allowance. The trace cap is inclusive and applies independently of DBCs; 1 GiB plus one byte is rejected clearly. Defaults need no environment-variable edit. Document the limits and preserve explicit administrator overrides without silently weakening existing server/LAN deployments.
- request-AC2 -> This backlog slice. Proof deferred to implementation closeout. Required evidence for request-AC2: Upload spooling, ASC parsing, indexing and decoding avoid whole-file text/byte buffers and eager full-trace signal materialization; use bounded batches, disk-backed indexes and bounded browser responses. Original timestamps, source ordering for ties, channels including sparse channel 9, standard/extended IDs, direction, DLC and payload remain exact. No source mutation, downsampling at ingestion or silent frame dropping is allowed.
- request-AC3 -> This backlog slice. Proof deferred to implementation closeout. Required evidence for request-AC3: Upload, indexing and ready phases remain distinguishable with honest progress. Cancellation works during transfer and indexing, preserves the previously loaded analysis, removes staging data and never publishes a partial replacement. Size errors, corrupt input, insufficient space and interrupted work produce actionable errors and recoverable state.
- request-AC4 -> This backlog slice. Proof deferred to implementation closeout. Required evidence for request-AC4: On Windows 11 x64 with at least four CPU cores, 16 GiB RAM and local SSD storage, an exactly 1 GiB representative generated ASC imports and becomes usable within 15 minutes, peak combined local-service process-tree working set stays within 6 GiB and the dedicated browser working set within 2 GiB. After import, warm p95 latency across at least 20 interactions is <=2 s for a 200-row filtered trace page, <=3 s for two plotted signals at <=4,000 points each and <=1 s for two-signal A/B cursor lookup; indexing cancellation is acknowledged within 5 s. Record exact hardware/browser/build, fixture counts/DBC density and storage peaks; these are delivery acceptance budgets, not already measured claims.
- request-AC5 -> This backlog slice. Proof deferred to implementation closeout. Required evidence for request-AC5: A portable Windows x64 .exe bundles the local Python/FastAPI runtime, static UI, required native dependencies and supported format readers. A standard user with no Python, Node, WSL, Docker or administrator rights can double-click it, start a loopback-only service and open the existing browser UI once ready. No separate desktop web engine is required. Windows 11 x64 is the initial guaranteed target; other OS/architectures remain outside the new binary guarantee.
- request-AC7 -> This backlog slice. Proof deferred to implementation closeout. Required evidence for request-AC7: The packaged application works from paths containing spaces and non-ASCII characters, including a repository cloned on an accessible WSL UNC share without using WSL to run the app. It preserves native Windows drive and accessible UNC trace paths rather than rewriting them into Linux paths. Writable workspace, staging files and logs live in per-user Windows directories outside the clone; second launch reopens a compatible existing instance, handles occupied ports and incompatible versions explicitly, exposes a reliable stop action and preserves library/session restore after restart.
- request-AC8 -> This backlog slice. Proof deferred to implementation closeout. Required evidence for request-AC8: The local UI retains existing DBC loading/conflict handling, plots, trace filtering/pagination, cursors, statistics/integral, report, session restore and exports. Existing ASC/TRC/BLF and compatible raw-CAN MF4 support is preserved in the executable with packaged-format smoke coverage. The new 1 GiB performance guarantee applies only to ASC; no broader MF4/BLF size or vendor-compatibility guarantee is implied. The deployed static PWA and its text-only import behavior remain unchanged.
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
- Rationale: explicit delivery gate for the central capacity claim; start fixture/baseline work early, qualify the final frozen artifact after other slices.
