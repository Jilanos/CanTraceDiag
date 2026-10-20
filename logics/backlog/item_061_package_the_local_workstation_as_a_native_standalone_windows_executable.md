## item_061_package_the_local_workstation_as_a_native_standalone_windows_executable - Package the local workstation as a native standalone Windows executable
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: High
> Theme: Native Windows runtime
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.
> Indicators reviewed: 2026-10-20 09:20:27

# AI Context
The existing launcher requires WSL/Python and path normalization assumes Linux semantics. Create a portable Windows 11 x64 .exe bundling the supported local server and runtime; evaluate a conventional freezer such as PyInstaller during implementation, verify dependency hooks and include packaged static assets and all supported format readers. Any self-extraction is internal; no user-managed environment or build step.

# Problem
- The existing launcher requires WSL/Python and path normalization assumes Linux semantics.
- Native runtime libraries, frozen assets, workspace persistence and app shutdown are not yet proven in a portable Windows artifact.

# Scope
- In:
  - Priority rationale: required foundation for the authorized no-toolchain user experience; build after the import contract is established.
  - Create a portable Windows 11 x64 .exe bundling the supported local server and runtime; evaluate a conventional freezer such as PyInstaller during implementation, verify dependency hooks and include packaged static assets and all supported format readers. Any self-extraction is internal; no user-managed environment or build step.
  - Launch loopback only, retain existing Host/Origin/token protections, open the default browser after readiness, handle busy ports and repeat launches with a version-aware handshake rather than attaching to arbitrary or incompatible services.
  - Provide a discoverable stop action or controlled launcher window; browser closure semantics must be documented. Exit releases resources and makes restart possible; report launch failure visibly and provide per-user logs.
  - Keep Windows drive/UNC paths native; do not run current WSL path rewrite unconditionally. Support spaces/non-ASCII and launches from an accessible WSL UNC clone while storing caches/temp/workspace on native per-user writable storage. WSL-share source access may require an existing share, but runtime must never depend on WSL.
  - Verify import, DBC library/conflicts, plots/cursors/integral, trace/report, restore and existing exports through the bundled UI. Smoke-test ASC/TRC/BLF and compatible raw-CAN MF4 using synthetic examples; retain existing reader scope and diagnostics.
  - Run artifact tests with Python/Node/WSL unavailable to the launched process and in a clean standard-user Windows environment. Verify native dependencies are actually bundled, not accidentally imported from the build machine.
- Out:
  - No change to the deployed static PWA import engine or 1 GiB guarantee for non-ASC formats.

# Acceptance criteria
- AC1: Double-clicking the built executable in a clean standard-user Windows environment opens a usable loopback browser UI without installing runtimes or elevation.
- AC2: Native/UNC and non-ASCII paths, busy ports, repeated launch, explicit stop, logs and session/library restart behavior pass artifact-level checks.
- AC3: The frozen artifact preserves existing supported formats and diagnostic/export workflows with representative synthetic smoke coverage.

# AC Traceability
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
- Rationale: required foundation for the authorized no-toolchain user experience; build after the import contract is established.

# Tasks
- `task_049_deliver_standalone_windows_launch_and_one_gib_asc_analysis`

# Notes
- Task `task_049_deliver_standalone_windows_launch_and_one_gib_asc_analysis` was finished via `logics-manager flow finish task` on 2026-10-20.
