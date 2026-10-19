## prod_017_portable_windows_local_workstation_for_1_gib_asc_acquisitions - Portable Windows local workstation for 1 GiB ASC acquisitions
> Date: 2026-10-19
> Status: Proposed
> Related request: `req_034_deliver_a_standalone_windows_local_application_for_asc_traces_up_to_1_gib`
> Related backlog: `item_060_accept_inclusive_1_gib_asc_uploads_with_independent_dbc_limits_and_bounded_indexing`, `item_061_package_the_local_workstation_as_a_native_standalone_windows_executable`, `item_062_download_the_matching_windows_release_from_a_repository_launcher`, `item_063_build_validate_and_publish_windows_executables_with_versioned_release_assets`, `item_064_qualify_one_gib_asc_fidelity_resource_usage_and_diagnostic_responsiveness_on_windows`
> Related task: `task_049_deliver_standalone_windows_launch_and_one_gib_asc_analysis`
> Related architecture: (none yet)
> Reminder: Update status, linked refs, scope, decisions, success signals, and open questions when you edit this doc.

# Overview
Make large ASC diagnostics accessible through a self-contained Windows local service and the familiar browser interface, obtained in a double-click flow from a clone.

# Goals
- Analyze a complete 1 GiB ASC with bounded memory and measured interaction performance.
- Deliver a version-matched Windows executable without Python, WSL or administrator setup.
- Preserve diagnostic behavior, existing local format support and the independently deployed web product.

# Non-goals
- Increase static-PWA trace capacity, replace the web engine or silently switch the public website to a server.
- Guarantee 1 GiB MF4/BLF/TRC or arbitrary vendor MDF compatibility; add CAN FD/XL support.
- Ship binaries in Git, build on the end-user machine, create an Electron shell or add cloud uploads.
- Guarantee Windows ARM64/macOS/Linux packaged executables or require paid signing infrastructure.

# Scope and guardrails
- Windows 11 x64 portable local service and existing browser UI; no Python, Node, WSL or administrator installation.
- Inclusive ASC trace limit: 1,073,741,824 bytes; independent uploaded DBC allowance: 64 MiB; multipart-envelope allowance: 8 MiB.
- Existing local ASC/TRC/BLF/raw-CAN MF4 support is retained; only ASC receives the new full-size qualification.
- The canonical hosted static PWA remains an independent delivery path. Native Windows packaging must not route its files to the hosted service.

# Key product decisions
- Double-click a root-level repository launcher to retrieve the executable from the matching published release. No binaries in Git and no end-user build.
- Require version, source provenance, architecture and SHA-256 verification before execution; reuse matching verified cache offline.
- A development checkout without a matching published binary explains how to select a release tag, rather than silently downloading latest.
- Use native per-user storage for workspace/cache/logs and support accessible UNC clone/source paths without rewriting them to Linux paths.
- Start loopback service, open the familiar UI when ready and expose a reliable stop action. Preserve DBC library and session restore.
- Initial qualification machine: Windows 11 x64, four or more cores, 16 GiB RAM, SSD. These scoping assumptions are targets to validate.

# User flow
```mermaid
flowchart LR
    A[Clone released source] --> B[Double click launcher]
    B --> C[Resolve matching release]
    C --> D[Verify executable and cache]
    D --> E[Start local service]
    E --> F[Open browser workspace]
    F --> G[Import ASC up to 1 GiB]
    G --> H[Analyze and restore locally]
```

# Success signals
- The final executable imports a representative, decoded 1 GiB ASC in at most 15 minutes on the reference configuration.
- Peak working set stays within 6 GiB for the service process tree and 2 GiB for the dedicated browser.
- Warm p95 latency is at most 2 s for a filtered 200-row page, 3 s for two 4,000-point signal plots, and 1 s for two-signal A/B cursor queries; indexing cancellation acknowledgement is at most 5 s.
- A clean standard-user Windows environment can run the exact verified release without development runtimes; subsequent cached launch works offline.
- Full-size qualification and compact automated tests preserve raw frame counts/values, existing workflows and source hashes. Operational files remain external.

# Open questions and implementation decisions
- No unanswered operator decision blocks scoping. Windows 11 x64, byte budgets and resource targets are explicit initial assumptions.
- Choose and validate the freezer and native dependency hooks during the first packaging wave; the .exe interface and autonomous-runtime requirement are fixed.
- A matching Windows release asset is a delivery dependency; no such artifact exists yet. Test release lookup and publication together.
- Signing credentials are not required for this scope; document actual unsigned status unless an identity is supplied later.
- The external acquisition is supplementary manual evidence if available; generated full-size qualification is mandatory and independent.

# References
- Product back-reference: `req_034_deliver_a_standalone_windows_local_application_for_asc_traces_up_to_1_gib`
- Task back-reference: `task_049_deliver_standalone_windows_launch_and_one_gib_asc_analysis`
