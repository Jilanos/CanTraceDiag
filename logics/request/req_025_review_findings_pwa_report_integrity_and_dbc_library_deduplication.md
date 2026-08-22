## req_025_review_findings_pwa_report_integrity_and_dbc_library_deduplication - Review findings: PWA report integrity and DBC library deduplication
> From version: 1.0.0
> Schema version: 1.0
> Status: Draft
> Understanding: 90%
> Confidence: 85%
> Complexity: Medium
> Theme: General
> Reminder: Update status/understanding/confidence and linked backlog/task references when you edit this doc.

# AI Context
- Summary: Capture two reproduced PWA data-integrity defects found during the 2026-08-22 project review.
- Keywords: review, findings, pwa, report, integrity, dbc, library, deduplication
- Use when: Deciding whether to correct PWA anomaly counts or strengthen content-based DBC deduplication.
- Skip when: Working on the already-captured large-file PWA migration, release deployment, or Python backend behavior.

# Needs
- Preserve exact anomaly multiplicities in the browser-local diagnostic report. The PWA currently reports one occurrence per distinct event type, even when the imported trace contains repeated events of that type.
- Make browser-local DBC deduplication identify file content strongly enough that two distinct DBC files cannot silently replace one another in the library because their short hashes collide.
- Add focused regression coverage for both defects before treating them as addressed.

# Context
- Review date: 2026-08-22. The working tree was clean before this request was created.
- Evidence for anomaly undercounting: `LocalTraceStore.eventTypes()` returns a unique sorted list at `spikes/pwa-local-engine/src/store.ts:81`, then `LocalPwaBackend.report()` increments each unique value once at `spikes/pwa-local-engine/src/local-backend.ts:146`. A direct Node reproduction imported two `ErrorFrame` events; `report()` returned `events: 2` but `anomalies.asc_events.ErrorFrame: 1`.
- Existing PWA coverage does not assert anomaly multiplicities: `spikes/pwa-local-engine/tests/local-backend.test.ts:233` checks report frame and path fields only. The normal fixture has one event of each type, so the browser smoke output cannot expose this defect.
- Evidence for DBC replacement: `digestText()` uses 32-bit FNV-1a at `spikes/pwa-local-engine/src/product-backend.ts:215`, and `saveDbcs()` keys its map by that digest at `spikes/pwa-local-engine/src/product-backend.ts:196`. The distinct prefixes `costarring` and `liquid` produce the same digest; when each was followed by the same valid DBC body and both files were uploaded, the stored library contained only `second.dbc` under digest `a0327bb6`.
- The Python reference library uses SHA-256 (`src/cantracediag/workspace.py:129` and `src/cantracediag/workspace.py:274`), so the browser-local behavior is also a parity divergence.
- Existing validations all passed despite these findings: `.venv/bin/ruff check .`; `.venv/bin/pytest` (`166 passed`, one dependency deprecation warning); Node PWA tests (`24 passed`); PWA build; and the Chromium browser smoke (`ok: true`, zero application API calls).
- Already-captured work was excluded: chunked large-file import and durable browser storage remain in `task_021_migrer_l_ui_produit_vers_la_pwa_local_first_avec_parite_mvp`; release/deployment remediation remains in `task_031_orchestrer_la_remediation_de_l_audit_cantracediag`.

# Scope boundaries
- In: PWA event-count accuracy, collision-safe DBC content identity, and focused browser-local regression tests.
- Out: large-file import architecture, OPFS/IndexedDB migration, broader DBC grammar parity, Python backend changes, release deployment, and unrelated style refactors.

# Priority
- Priority: Medium
- Rationale: Both findings can misstate or replace user diagnostic inputs, but they are bounded to the browser-local path and have deterministic reproductions.

# Acceptance criteria
- AC1: For a browser-local trace containing repeated events of one type, the report returns the exact count for that type and the displayed diagnostic report shows the same multiplicity.
- AC2: Two distinct DBC contents remain distinct library entries even when a legacy 32-bit hash function would collide, while byte-identical DBC contents are still deduplicated.
- AC3: Automated PWA tests cover at least one repeated-event report and one deterministic content-identity collision case, and fail against the reviewed implementation.
- AC4: The standard Node PWA tests, PWA build, Chromium browser smoke, Python tests, and Ruff checks continue to pass after any future implementation.
- AC5: Any future backlog promotion remains bounded to these two reproduced defects and does not absorb the already-tracked PWA migration or release work.

# Definition of Ready (DoR)
- [x] Problem statement is explicit and user impact is clear.
- [x] Scope boundaries (in/out) are explicit.
- [x] Acceptance criteria are testable.
- [x] Dependencies and known risks are listed.

# Companion docs
- Product brief(s): (none yet)
- Architecture decision(s): (none yet)

# References
- `spikes/pwa-local-engine/src/store.ts`
- `spikes/pwa-local-engine/src/local-backend.ts`
- `spikes/pwa-local-engine/src/product-backend.ts`
- `spikes/pwa-local-engine/tests/local-backend.test.ts`
- `src/cantracediag/workspace.py`
- `.github/workflows/ci.yml`

# Backlog
- none
