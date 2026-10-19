## item_062_download_the_matching_windows_release_from_a_repository_launcher - Download the matching Windows release from a repository launcher
> From version: 1.0.0
> Schema version: 1.0
> Status: Ready
> Understanding: 90%
> Confidence: 85%
> Progress: 0%
> Complexity: High
> Theme: Clone bootstrap and version matching
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.
> Indicators reviewed: 2026-10-19 11:45:49

# AI Context
A clone does not contain a usable native executable and arbitrary latest downloads can disagree with the checked-out source. Add an obvious root-level .cmd/PowerShell bootstrap that resolves its location without a configured repository path or developer toolchain. Use OS-provided facilities, handle spaces/non-ASCII and accessible UNC paths, and never require a global execution-policy change.

# Problem
- A clone does not contain a usable native executable and arbitrary latest downloads can disagree with the checked-out source.

# Scope
- In:
  - Priority rationale: completes the requested clone-to-double-click path after an artifact naming/provenance contract exists.
  - Add an obvious root-level .cmd/PowerShell bootstrap that resolves its location without a configured repository path or developer toolchain. Use OS-provided facilities, handle spaces/non-ASCII and accessible UNC paths, and never require a global execution-policy change.
  - Resolve the canonical project version and matching release descriptor, including source revision and architecture. Tagged checkouts must match exactly; untagged checkouts may launch only if verified as the same released source. If no matching published asset exists, explain how to check out a release tag. Never silently select latest or run code from an arbitrary download URL.
  - Use canonical HTTPS release assets and published SHA-256/provenance metadata; stream to a temporary per-user cache entry, verify before atomic promotion/execution, and handle concurrent launches. Do not put binaries/downloads in tracked files or require write access to the clone.
  - Cache by version/architecture with integrity revalidation; offline relaunch uses only a matching valid cache. Recover from missing release assets, interrupted transfer, offline first run, wrong architecture and corruption while preserving the last valid cached asset.
  - Document first retrieval versus later offline operation, visible runtime version, cache cleanup, failure instructions and optional existing source/WSL workflow without presenting it as a required fallback.
- Out:
  - No change to the deployed static PWA import engine or 1 GiB guarantee for non-ASC formats.

# Acceptance criteria
- AC1: A fresh supported clone starts the exact published Windows artifact by double-click, without a preinstalled developer toolchain and without committed binaries.
- AC2: Version/source/checksum/architecture mismatches and unpublished revisions fail clearly; no latest or unverified execution fallback occurs.
- AC3: Matching cached launches work offline, interrupted downloads recover atomically and concurrent launches do not corrupt cache.

# AC Traceability
- request-AC6 -> This backlog slice. Proof deferred to implementation closeout. Required evidence for request-AC6: A clearly named root-level Windows launcher included in a fresh clone downloads and launches the release executable associated with that checkout, from the canonical release origin, verifies version/source provenance and SHA-256, and caches it outside Git. No binary is committed. A tagged checkout uses that exact release; a checkout with no matching published binary fails with clear instructions to select a published release tag, never silently choosing latest. Subsequent launches use the matching verified cache offline; missing assets, network failures, incomplete downloads, wrong architecture and checksum mismatch fail without executing unverified bytes.
- request-AC7 -> This backlog slice. Proof deferred to implementation closeout. Required evidence for request-AC7: The packaged application works from paths containing spaces and non-ASCII characters, including a repository cloned on an accessible WSL UNC share without using WSL to run the app. It preserves native Windows drive and accessible UNC trace paths rather than rewriting them into Linux paths. Writable workspace, staging files and logs live in per-user Windows directories outside the clone; second launch reopens a compatible existing instance, handles occupied ports and incompatible versions explicitly, exposes a reliable stop action and preserves library/session restore after restart.
- request-AC9 -> This backlog slice. Proof deferred to implementation closeout. Required evidence for request-AC9: Windows CI builds and smoke-tests the exact distributable without relying on an installed developer runtime, and publishes executable plus checksum/provenance metadata on the same versioned release after required validation. The launcher can resolve that release without coupling Windows availability to the web deployment success. Preserve existing PWA/Docker release checks, document any release-graph changes, runtime distribution notices, first-download/offline behavior, stop/log/cache locations and unsigned executable status if no signing identity exists.
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
- Rationale: completes the requested clone-to-double-click path after an artifact naming/provenance contract exists.
