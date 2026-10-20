## item_062_download_the_matching_windows_release_from_a_repository_launcher - Download the matching Windows release from a repository launcher
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: High
> Theme: Clone bootstrap and version matching
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.
> Indicators reviewed: 2026-10-20 09:20:28

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
- request-AC6 -> This backlog slice. Proof: root `CanTraceDiag.cmd` + `packaging/windows/launcher.ps1` (0dbf7b6, 6646d96): resolves v<version> from the checkout, verifies provenance (version, tag, x64, exact commit) and SHA-256 before execution, caches per user, no latest fallback; `packaging/windows/test_launcher.py` 13/13 on CI (missing release, dev commit refused, wrong arch, checksum mismatch, incomplete/altered download, offline cache, corrupted cache, network failure, packed refs, explicit -Release, PowerShell 7); fresh Windows clone of v1.4.0 downloaded, verified (9344b2fc...) and ran the published exe, then ran it offline from cache; no binary in Git.
- request-AC7 -> This backlog slice. Proof: native paths kept on a Windows backend (`normalize_local_path`, `tests/test_paths.py::test_native_windows_keeps_drive_and_unc_paths`); per-user `%LOCALAPPDATA%\CanTraceDiag` data/logs/instance; second launch attaches, other version refused, occupied/excluded ports skipped by bound-socket fallback, `--stop` and console close stop the service (`tests/test_desktop.py`); smoke 16/16 covers non-ASCII and spaced paths, occupied port, attach, stop and restart restore; launcher test passes from a `\\wsl.localhost` checkout; external acquisition read in place from a `\\wsl.localhost` share.
- request-AC9 -> This backlog slice. Proof: `.github/workflows/windows.yml` builds, smoke-tests and launcher-tests the exact exe on every push (CI 39283800645 green) and on the tag; `publish-windows` depends only on validation and that build, checks SHA-256/provenance and publishes exe, .sha256, provenance and THIRD_PARTY_NOTICES.txt (release workflow 39286947315 green, all 7 jobs); PWA/Docker jobs unchanged; README documents first download, offline reuse, stop/log/cache locations, notices and unsigned status; ADR 0008 records the release-graph change.
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
- Rationale: completes the requested clone-to-double-click path after an artifact naming/provenance contract exists.

# Tasks
- `task_049_deliver_standalone_windows_launch_and_one_gib_asc_analysis`

# Notes
- Task `task_049_deliver_standalone_windows_launch_and_one_gib_asc_analysis` was finished via `logics-manager flow finish task` on 2026-10-20.
