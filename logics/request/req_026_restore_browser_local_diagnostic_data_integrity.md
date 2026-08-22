## req_026_restore_browser_local_diagnostic_data_integrity - Restore browser-local diagnostic data integrity
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Complexity: Medium
> Theme: Browser-local diagnostic integrity
> Reminder: Update status/understanding/confidence and linked backlog/task references when you edit this doc.
> Indicators reviewed: 2026-08-22 12:37:56

# AI Context
- Summary: Remediate two reproduced PWA integrity failures: repeated anomaly undercounting and collision-prone DBC library identity.
- Keywords: restore, browser, local, diagnostic, data, integrity
- Use when: Planning, implementing, or validating the linked anomaly-count and DBC-identity backlog slices.
- Skip when: Working on large-file persistence, DBC grammar expansion, Python-only behavior, or unrelated release infrastructure.

# Needs
- Make browser-local diagnostic reports preserve the exact multiplicity of every imported anomaly type instead of reducing repeated events to one occurrence.
- Make browser-local DBC library identity collision-safe so distinct file contents can coexist and byte-identical contents remain deduplicated.
- Protect both data-integrity contracts with deterministic regression tests and parity checks against the Python reference behavior.

# Context
- The 2026-08-22 review reproduced a report containing two ErrorFrame events while anomalies.asc_events.ErrorFrame was one because the store exposes a unique event-type list and the report counts that list.
- The review also reproduced two distinct, parseable DBC contents with the same 32-bit FNV-1a digest; the browser-local library retained only the second entry because the digest is the map key.
- The Python reference library uses SHA-256 for content identity and its report summary preserves event counts, making both findings browser-local parity divergences.
- The current Python suite, Node PWA suite, PWA build, and Chromium smoke all pass, demonstrating that focused regression coverage is required rather than broad test repair.
- This request is limited to the two reproduced findings. Chunked large-file import, durable trace storage, broader DBC grammar parity, and release-infrastructure remediation are already tracked elsewhere.
- Because this is a functional correction intended for release, delivery must follow the repository release policy: validate locally, commit implementation, prepare the next SemVer patch, push, wait for CI on that exact commit, create and push one annotated tag, verify the tag-triggered release workflow, and record evidence.

# Acceptance criteria
- AC1: For browser-local imports, the diagnostic report returns the exact count of each event type, including repeated events, while the trace event filter continues to expose each available type once.
- AC2: The rendered PWA report displays the same exact anomaly counts returned by the local backend and remains contract-compatible with the Python reference report.
- AC3: Browser-local DBC identity uses collision-safe content semantics: distinct contents remain separate library entries and byte-identical contents are deduplicated regardless of filename.
- AC4: Existing valid browser-local library entries remain usable through a documented compatibility or migration path; the change does not silently discard recoverable entries, and an already-overwritten legacy collision is not falsely claimed as recoverable.
- AC5: Automated tests reproduce repeated-event counting and a deterministic legacy 32-bit collision, verify Python/PWA parity for the affected payloads, and the standard Python, Ruff, Node, build, and Chromium smoke validations pass.
- AC6: The implementation and version-preparation commits, successful CI run, annotated patch tag, and tag-triggered release outcome are recorded in the task closeout before the chain is marked done.

# Definition of Ready (DoR)
- [x] Problem statement is explicit and user impact is clear.
- [x] Scope boundaries (in/out) are explicit.
- [x] Acceptance criteria are testable.
- [x] Dependencies and known risks are listed.

# Companion docs
- Product brief(s): `prod_012_trustworthy_browser_local_diagnostics`
- Architecture decision(s): (none yet)

# References
- logics/request/req_025_review_findings_pwa_report_integrity_and_dbc_library_deduplication.md
- spikes/pwa-local-engine/src/store.ts
- spikes/pwa-local-engine/src/local-backend.ts
- spikes/pwa-local-engine/src/product-backend.ts
- spikes/pwa-local-engine/tests/local-backend.test.ts
- spikes/pwa-local-engine/browser-smoke.mjs
- src/cantracediag/workspace.py
- src/cantracediag/store.py
- src/cantracediag/api.py
- .github/workflows/ci.yml
- logics/release/contract.json

# Backlog
- `item_047_preserve_exact_anomaly_counts_in_browser_local_reports`
- `item_048_adopt_collision_safe_browser_local_dbc_content_identity`
