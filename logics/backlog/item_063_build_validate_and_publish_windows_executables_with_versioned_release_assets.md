## item_063_build_validate_and_publish_windows_executables_with_versioned_release_assets - Build validate and publish Windows executables with versioned release assets
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: High
> Theme: Desktop CI and release delivery
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.
> Indicators reviewed: 2026-10-20 09:20:27

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
- request-AC5 -> This backlog slice. Proof: PyInstaller one-file exe from `packaging/windows/CanTraceDiag.spec` with pinned constraints (856b484): Python, FastAPI/Uvicorn, DuckDB, PyArrow, ASC/TRC/BLF/MF4 readers and static UI bundled; loopback-only service opening the default browser (`cantracediag.desktop`); `packaging/windows/smoke.py` 16/16 on the published v1.4.0 exe with a scrubbed environment (no Python on PATH, no PYTHON* variables), on GitHub Actions run 39283800645 and on this Windows 11 machine; README documents Windows 11 x64 as the only guaranteed target.
- request-AC6 -> This backlog slice. Proof: root `CanTraceDiag.cmd` + `packaging/windows/launcher.ps1` (0dbf7b6, 6646d96): resolves v<version> from the checkout, verifies provenance (version, tag, x64, exact commit) and SHA-256 before execution, caches per user, no latest fallback; `packaging/windows/test_launcher.py` 13/13 on CI (missing release, dev commit refused, wrong arch, checksum mismatch, incomplete/altered download, offline cache, corrupted cache, network failure, packed refs, explicit -Release, PowerShell 7); fresh Windows clone of v1.4.0 downloaded, verified (9344b2fc...) and ran the published exe, then ran it offline from cache; no binary in Git.
- request-AC8 -> This backlog slice. Proof: existing local UI unchanged and its Playwright suite green (344 pytest incl. E2E); packaged smoke imports ASC+DBC, TRC, BLF and raw-CAN MF4 (chardet mypyc modules bundled for asammdf), plots, trace paging, cursors, report, CSV and raw ASC export, restore; README states the 1 GiB guarantee is ASC-only; PWA untouched: 86 node tests, build and browser smoke `ok: true`, release deploy job green and https://cantracediag.paulmondou.fr/ 200 after v1.4.0.
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
- Rationale: the bootstrap cannot be delivered until corresponding verified assets exist on a release.

# Tasks
- `task_049_deliver_standalone_windows_launch_and_one_gib_asc_analysis`

# Notes
- Task `task_049_deliver_standalone_windows_launch_and_one_gib_asc_analysis` was finished via `logics-manager flow finish task` on 2026-10-20.
