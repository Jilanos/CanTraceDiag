## item_063_build_validate_and_publish_windows_executables_with_versioned_release_assets - Build validate and publish Windows executables with versioned release assets
> From version: 1.0.0
> Schema version: 1.0
> Status: Ready
> Understanding: 90%
> Confidence: 85%
> Progress: 0%
> Complexity: High
> Theme: Desktop CI and release delivery
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.
> Indicators reviewed: 2026-10-19 11:45:49

# AI Context
The release workflow publishes a static web container and creates a release only after production deployment; it publishes no Windows artifact. Add a Windows build/test lane with recorded dependency and tool versions, application version/source provenance, required bundled assets/native libraries and distribution notices. Publish a clearly named x64 .exe and SHA-256/provenance manifest on the matching versioned release.

# Problem
- The release workflow publishes a static web container and creates a release only after production deployment; it publishes no Windows artifact.

# Scope
- In:
  - Priority rationale: the bootstrap cannot be delivered until corresponding verified assets exist on a release.
  - Add a Windows build/test lane with recorded dependency and tool versions, application version/source provenance, required bundled assets/native libraries and distribution notices. Publish a clearly named x64 .exe and SHA-256/provenance manifest on the matching versioned release.
  - Gate executable publication on exact-artifact smoke results and required checks. Retain PWA/Node, Python and Docker validation and web deployment behavior; adjust the release DAG deliberately so a failed web deployment cannot prevent access to an independently validated Windows release artifact. Never expose incomplete draft assets as ready.
  - Test the bootstrap against the asset/metadata naming contract, including versions with missing assets and tag/source disagreement. Record actual binary digest, build SHA, CI run and release asset URL before closeout.
  - Document Windows installation-free startup, minimum hardware, byte-precise limits, existing MF4 scope, stop/restart, storage paths, offline/cache behavior and unsigned status. Update architecture docs to distinguish hosted PWA from the standalone local service.
  - Code signing is optional without supplied credentials; do not disable OS protection or assert unsigned builds are signed. Keep packaging decisions and any release limitations reviewable.
- Out:
  - No change to the deployed static PWA import engine or 1 GiB guarantee for non-ASC formats.

# Acceptance criteria
- AC1: Windows CI produces and tests the same executable it publishes, with verifiable version/source/hash metadata and required runtime assets.
- AC2: A successful Windows artifact is discoverable by the clone bootstrap independently of web deployment success; existing web release checks remain effective.
- AC3: Documentation and release evidence match the actual supported platform, limits, offline behavior and signature status.

# AC Traceability
- request-AC5 -> This backlog slice. Proof deferred to implementation closeout. Required evidence for request-AC5: A portable Windows x64 .exe bundles the local Python/FastAPI runtime, static UI, required native dependencies and supported format readers. A standard user with no Python, Node, WSL, Docker or administrator rights can double-click it, start a loopback-only service and open the existing browser UI once ready. No separate desktop web engine is required. Windows 11 x64 is the initial guaranteed target; other OS/architectures remain outside the new binary guarantee.
- request-AC6 -> This backlog slice. Proof deferred to implementation closeout. Required evidence for request-AC6: A clearly named root-level Windows launcher included in a fresh clone downloads and launches the release executable associated with that checkout, from the canonical release origin, verifies version/source provenance and SHA-256, and caches it outside Git. No binary is committed. A tagged checkout uses that exact release; a checkout with no matching published binary fails with clear instructions to select a published release tag, never silently choosing latest. Subsequent launches use the matching verified cache offline; missing assets, network failures, incomplete downloads, wrong architecture and checksum mismatch fail without executing unverified bytes.
- request-AC8 -> This backlog slice. Proof deferred to implementation closeout. Required evidence for request-AC8: The local UI retains existing DBC loading/conflict handling, plots, trace filtering/pagination, cursors, statistics/integral, report, session restore and exports. Existing ASC/TRC/BLF and compatible raw-CAN MF4 support is preserved in the executable with packaged-format smoke coverage. The new 1 GiB performance guarantee applies only to ASC; no broader MF4/BLF size or vendor-compatibility guarantee is implied. The deployed static PWA and its text-only import behavior remain unchanged.
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
- Rationale: the bootstrap cannot be delivered until corresponding verified assets exist on a release.
