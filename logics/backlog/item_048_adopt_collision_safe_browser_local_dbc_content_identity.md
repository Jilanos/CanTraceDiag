## item_048_adopt_collision_safe_browser_local_dbc_content_identity - Adopt collision-safe browser-local DBC content identity
> From version: 1.0.0
> Schema version: 1.0
> Status: In progress
> Understanding: 90%
> Confidence: 85%
> Progress: 10%
> Complexity: Medium
> Theme: Local library data integrity
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.
> Indicators reviewed: 2026-08-22 12:25:36

# AI Context
- Summary: Replace sole reliance on the browser library's 32-bit digest while preserving deduplication and legacy-entry compatibility.
- Keywords: adopt, collision, safe, browser, local, dbc, content, identity
- Use when: Implementing PWA DBC identity, library migration, selection, reload, or collision regression tests.
- Skip when: Moving storage to OPFS or IndexedDB, changing DBC parsing, or recovering content that was already overwritten.

# Problem
- The browser-local library uses a 32-bit FNV-1a digest as its sole map key, so distinct DBC contents with the same digest silently overwrite one another.
- Changing the identifier without an explicit compatibility path could make valid entries stored under the current library schema unreachable.

# Scope
- In:
  - Replace sole reliance on the 32-bit digest with collision-safe content identity suitable for browser execution and stable library selection.
  - Keep byte-identical content deduplication independent of filenames and preserve the existing 20-entry retention policy unless a migration requires a documented equivalent.
  - Define and implement a compatibility path for valid entries stored under the current library key, including explicit handling of malformed entries and the fact that previously overwritten content cannot be reconstructed.
  - Add deterministic coverage using two distinct DBC contents that share the reviewed legacy digest plus coverage for identical-content deduplication and library reuse by identifier.
  - Verify the browser-local behavior against the Python reference content-identity semantics.
- Out:
  - Moving trace or DBC persistence to OPFS or IndexedDB as part of this correction.
  - Recovering content that is no longer present in local storage.
  - Changing DBC parsing, conflict resolution, load ordering, or the visible library workflow except where identifier compatibility requires it.

# Acceptance criteria
- AC1: The deterministic legacy collision pair is retained as two separate usable library entries with different new identifiers.
- AC2: Two byte-identical DBC uploads with different filenames produce one content entry and remain selectable for a later trace import.
- AC3: A valid legacy library payload is migrated or read compatibly without silent loss, malformed entries fail safely, and the compatibility behavior is covered by automated tests.
- AC4: The local library list and import-selection contracts continue to return stable identifiers, names, last-used metadata, and successful DBC reuse after a reload.
- AC5: Focused Node tests, the full PWA suite, PWA build, Chromium smoke, Python tests, and Ruff checks pass after the correction.

# AC Traceability
- request-AC3 -> This backlog slice. Proof: AC1: The deterministic legacy collision pair is retained as two separate usable library entries with different new identifiers.
- request-AC4 -> This backlog slice. Proof: AC2: Two byte-identical DBC uploads with different filenames produce one content entry and remain selectable for a later trace import.
- request-AC5 -> This backlog slice. Proof: AC3: A valid legacy library payload is migrated or read compatibly without silent loss, malformed entries fail safely, and the compatibility behavior is covered by automated tests.
- request-AC6 -> This backlog slice. Proof: AC4: The local library list and import-selection contracts continue to return stable identifiers, names, last-used metadata, and successful DBC reuse after a reload.

# Decision framing
- Product framing: Not needed
- Architecture framing: Not needed

# Links
- Product brief(s): `prod_012_trustworthy_browser_local_diagnostics`
- Architecture decision(s): (none yet)
- Request: `req_026_restore_browser_local_diagnostic_data_integrity`
- Primary task(s): `task_044_deliver_browser_local_diagnostic_integrity_remediation`

# Priority
- Priority: High
- Rationale: Set by scaffold input or defaulted for grooming.
