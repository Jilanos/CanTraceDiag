## item_061_package_the_local_workstation_as_a_native_standalone_windows_executable - Package the local workstation as a native standalone Windows executable
> From version: 1.0.0
> Schema version: 1.0
> Status: Ready
> Understanding: 90%
> Confidence: 85%
> Progress: 0%
> Complexity: High
> Theme: Native Windows runtime
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.
> Indicators reviewed: 2026-10-19 11:45:49

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
- Rationale: required foundation for the authorized no-toolchain user experience; build after the import contract is established.
