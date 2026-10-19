## req_034_deliver_a_standalone_windows_local_application_for_asc_traces_up_to_1_gib - Deliver a standalone Windows local application for ASC traces up to 1 GiB
> From version: 1.0.0
> Schema version: 1.0
> Status: Ready
> Understanding: 90%
> Confidence: 85%
> Complexity: High
> Theme: Standalone Windows local analysis and large ASC acquisitions
> Reminder: Update status/understanding/confidence and linked backlog/task references when you edit this doc.
> Indicators reviewed: 2026-10-19 11:45:48

# AI Context
Scope the local Windows service and its distribution, using the existing Python engine. The hosted browser engine cannot fulfill this capacity promise. Size-boundary, native-runtime and measured responsiveness evidence are all required; a raised environment limit alone is insufficient.

# Needs
- Provide an autonomous Windows executable for an operator currently using only the static website; cloning the repository exposes an obvious double-click launcher that retrieves the corresponding release.
- Read and analyze ASC traces up to an inclusive 1 GiB without splitting the acquisition, installing a development toolchain or changing environment variables.
- Keep the familiar diagnostic UI and validate usable navigation, progress and cancellation on representative large inputs.

# Context
- Operator decisions: genuine autonomous Windows .exe without Python/WSL installation; versioned launcher downloads a matching release instead of committing binaries; inclusive ASC 1 GiB guarantee with separate DBC margin; preserve the web application.
- Current local Python/FastAPI implementation already streams import in 50,000-item batches into a disk-backed session store and supports asynchronous jobs, cancellation, DBC library and restore. Existing Windows launcher assumes WSL and a preinstalled virtual environment; it is not a standalone distribution.
- Current aggregate upload default is 512 MiB across trace and DBCs. Merely setting it to 1024 MiB cannot accept a full 1 GiB trace plus multipart overhead and DBCs; independent limits and end-to-end boundary tests are required.
- The static PWA currently calls File.text(), splits the whole trace and eagerly decodes samples. This request uses the existing server-backed architecture locally and does not attempt to lift the browser string/memory limit.
- Read-only inspection of an external converted/concatenated ASC found 668,097,985 bytes, 10,613,470 recognized frames, 45 IDs, channels 1 and 9, duration about 5,389.79 s, no ASC syntax anomaly, no backwards timestamp and no gap over one second. This is structural evidence, not a complete import/performance qualification. No recording is included in Git.
- Local MF4 support already exists for compatible raw classic-CAN MDF4 bus logging, including constrained unfinalized recovery; the static PWA does not support MF4. Preserve this local capability without claiming 1 GiB MF4 qualification.
- Native Windows packaging must inspect Linux-specific path normalization, per-user paths, native DuckDB/PyArrow/MDF reader libraries, frozen static asset discovery, browser opening and process lifecycle. Raising a limit alone does not establish an autonomous or responsive product.
- Scoping assumptions selected for a concrete first delivery: Windows 11 x64, standard user, existing browser, four cores/16 GiB RAM/SSD reference machine, 64 MiB uploaded-DBC allowance, 8 MiB envelope allowance, internet only for first retrieval. These are implementation acceptance targets, not observed capabilities.
- Release resolution must be deterministic: exact published release for tagged/source-matching checkouts; unavailable development commits get an actionable failure rather than arbitrary latest fallback. Do not promise a binary for every development commit. Code signing is not a prerequisite unless a signing identity is supplied; document unsigned status instead of bypassing Windows protections.
- This request creates workflow documentation only. Do not implement, install packaging dependencies, publish a release or modify operational recordings during scoping. Existing architecture documentation must later describe Windows local delivery alongside the unchanged canonical web artifact.

# Acceptance criteria
- AC1: The Windows local application accepts a classic-CAN ASC trace of exactly 1,073,741,824 bytes through the normal browser file picker, with an independent 64 MiB aggregate uploaded-DBC budget and 8 MiB multipart-envelope allowance. The trace cap is inclusive and applies independently of DBCs; 1 GiB plus one byte is rejected clearly. Defaults need no environment-variable edit. Document the limits and preserve explicit administrator overrides without silently weakening existing server/LAN deployments.
- AC2: Upload spooling, ASC parsing, indexing and decoding avoid whole-file text/byte buffers and eager full-trace signal materialization; use bounded batches, disk-backed indexes and bounded browser responses. Original timestamps, source ordering for ties, channels including sparse channel 9, standard/extended IDs, direction, DLC and payload remain exact. No source mutation, downsampling at ingestion or silent frame dropping is allowed.
- AC3: Upload, indexing and ready phases remain distinguishable with honest progress. Cancellation works during transfer and indexing, preserves the previously loaded analysis, removes staging data and never publishes a partial replacement. Size errors, corrupt input, insufficient space and interrupted work produce actionable errors and recoverable state.
- AC4: On Windows 11 x64 with at least four CPU cores, 16 GiB RAM and local SSD storage, an exactly 1 GiB representative generated ASC imports and becomes usable within 15 minutes, peak combined local-service process-tree working set stays within 6 GiB and the dedicated browser working set within 2 GiB. After import, warm p95 latency across at least 20 interactions is <=2 s for a 200-row filtered trace page, <=3 s for two plotted signals at <=4,000 points each and <=1 s for two-signal A/B cursor lookup; indexing cancellation is acknowledged within 5 s. Record exact hardware/browser/build, fixture counts/DBC density and storage peaks; these are delivery acceptance budgets, not already measured claims.
- AC5: A portable Windows x64 .exe bundles the local Python/FastAPI runtime, static UI, required native dependencies and supported format readers. A standard user with no Python, Node, WSL, Docker or administrator rights can double-click it, start a loopback-only service and open the existing browser UI once ready. No separate desktop web engine is required. Windows 11 x64 is the initial guaranteed target; other OS/architectures remain outside the new binary guarantee.
- AC6: A clearly named root-level Windows launcher included in a fresh clone downloads and launches the release executable associated with that checkout, from the canonical release origin, verifies version/source provenance and SHA-256, and caches it outside Git. No binary is committed. A tagged checkout uses that exact release; a checkout with no matching published binary fails with clear instructions to select a published release tag, never silently choosing latest. Subsequent launches use the matching verified cache offline; missing assets, network failures, incomplete downloads, wrong architecture and checksum mismatch fail without executing unverified bytes.
- AC7: The packaged application works from paths containing spaces and non-ASCII characters, including a repository cloned on an accessible WSL UNC share without using WSL to run the app. It preserves native Windows drive and accessible UNC trace paths rather than rewriting them into Linux paths. Writable workspace, staging files and logs live in per-user Windows directories outside the clone; second launch reopens a compatible existing instance, handles occupied ports and incompatible versions explicitly, exposes a reliable stop action and preserves library/session restore after restart.
- AC8: The local UI retains existing DBC loading/conflict handling, plots, trace filtering/pagination, cursors, statistics/integral, report, session restore and exports. Existing ASC/TRC/BLF and compatible raw-CAN MF4 support is preserved in the executable with packaged-format smoke coverage. The new 1 GiB performance guarantee applies only to ASC; no broader MF4/BLF size or vendor-compatibility guarantee is implied. The deployed static PWA and its text-only import behavior remain unchanged.
- AC9: Windows CI builds and smoke-tests the exact distributable without relying on an installed developer runtime, and publishes executable plus checksum/provenance metadata on the same versioned release after required validation. The launcher can resolve that release without coupling Windows availability to the web deployment success. Preserve existing PWA/Docker release checks, document any release-graph changes, runtime distribution notices, first-download/offline behavior, stop/log/cache locations and unsigned executable status if no signing identity exists.
- AC10: Boundary tests cover trace cap minus one/exact/plus one byte, separate DBC/envelope budgets, missing or misleading Content-Length and streaming enforcement. Generated fixtures cover multi-channel/extended IDs, equal timestamps, malformed records, cancellation/rollback and meaningful DBC decoding. Run a full 1 GiB Windows qualification plus the external roughly 637 MiB acquisition when available; publish only anonymized counts, hashes and timing/memory results, never operational traces, payloads, DBC contents or machine-specific paths. Closeout maps every criterion to evidence and records remaining platform limits.

# Definition of Ready (DoR)
- [x] Problem statement is explicit and user impact is clear.
- [x] Scope boundaries (in/out) are explicit.
- [x] Acceptance criteria are testable.
- [x] Dependencies and known risks are listed.

# Companion docs
- Product brief(s): `prod_017_portable_windows_local_workstation_for_1_gib_asc_acquisitions`
- Architecture decision(s): (none yet)

# References
- README.md
- pyproject.toml
- docs/architecture-pwa-canonique.md
- src/cantracediag/security.py
- src/cantracediag/api.py
- src/cantracediag/cli.py
- src/cantracediag/pipeline.py
- src/cantracediag/store.py
- src/cantracediag/workspace.py
- src/cantracediag/formats/asc.py
- src/cantracediag/formats/mf4.py
- src/cantracediag/web/js/import.js
- scripts/CanTraceDiag.cmd
- scripts/install-shortcut.ps1
- .github/workflows/release.yml
- tests/test_security.py
- tests/test_cli.py
- tests/test_store_pipeline.py
- tests/test_perf_budget.py
- tests/test_workspace.py
- tests/test_e2e_ui.py
- spikes/pwa-local-engine/src/product-backend.ts

# Backlog
- `item_060_accept_inclusive_1_gib_asc_uploads_with_independent_dbc_limits_and_bounded_indexing`
- `item_061_package_the_local_workstation_as_a_native_standalone_windows_executable`
- `item_062_download_the_matching_windows_release_from_a_repository_launcher`
- `item_063_build_validate_and_publish_windows_executables_with_versioned_release_assets`
- `item_064_qualify_one_gib_asc_fidelity_resource_usage_and_diagnostic_responsiveness_on_windows`
