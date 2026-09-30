## item_056_persist_and_preselect_the_exact_last_successful_dbc_load_set - Persist and preselect the exact last successful DBC load set
> From version: 1.0.0
> Schema version: 1.0
> Status: In progress
> Understanding: 90%
> Confidence: 85%
> Progress: 30%
> Complexity: Medium
> Theme: Repeat import defaults
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.
> Indicators reviewed: 2026-09-30 13:04:12

# AI Context
The PWA currently loses last-session names on reload, and the shared picker reapplies defaults to any empty set. Persist canonical digests and distinguish initial hydration from intentional uncheck-all.

# Problem
- PWA DBC history is volatile and filename-based UI matching can select the wrong content.
- The empty-set defaulting condition can override intentional uncheck-all choices.

# Scope
- In:
  - Priority rationale: repeated-load usability improvement independent of numeric integration; may be delivered before the integration slices.
  - Persist the exact ordered set of library content digests used by the last successfully completed trace import, including newly uploaded DBCs after insertion and reused library entries. Store it locally in the PWA and use the persistent workspace manifest on the server.
  - On initial picker setup after a browser reload or application restart, precheck only remembered digests still present in the library. DBCs with no matching frames in the trace still belong to the chosen set; do not substitute dbcs_used or recency-ranked files.
  - Use content identity rather than filenames: two different files with the same name remain distinct; identical content is selected once. Reuse the canonical library digest and respect its migration contract; do not create a second hashing algorithm.
  - Defaulting happens once per new picker state, after library/history hydration and before submitting a trace-only import. Preserve manual changes, including deselecting every entry, across modal reopen and background library refresh. Distinguish untouched empty selection from deliberately cleared selection.
  - Commit replacement history only after import completion and any required DBC conflict resolution and successful persistence. Failed, cancelled, or unresolved imports keep the previous successful set. A newly completed import seeds the next fresh picker state; edits for the current picker remain authoritative.
  - First use, missing or malformed history, deleted library entries, and storage unavailability degrade without arbitrary selections or blocked manual import. Handle legacy name-only history only when an exact name match is unique; ambiguous names remain unchecked. Purge clears library and remembered selection.
  - Browser coverage must import two DBCs, reload the page, verify prechecked entries, import a new trace without selecting DBCs again, and preserve manual uncheck-all. Add same-name/different-content, deleted entry, failed import, conflict resolution, purge, and server restart coverage.
- Out:
  - Restoring a full browser analysis session, automatically loading traces, and redefining DBC identity.

# Acceptance criteria
- AC1: A successful mixed uploaded/reused DBC load persists its ordered content-identity set and prechecks precisely the surviving entries after browser reload or server workspace restart.
- AC2: A trace-only subsequent load reuses the prechecked set without reopening the library; manual edits and uncheck-all survive reopening and refresh.
- AC3: Same-name content stays distinct, missing entries are skipped, unique legacy names migrate safely, failures and unresolved imports preserve prior history, and purge clears history.
- AC4: Focused adapter, workspace, and browser tests cover persistence lifecycle and storage failure without blocking manual import.

# AC Traceability
- request-AC4 -> This backlog slice. Proof: AC1: A successful mixed uploaded/reused DBC load persists its ordered content-identity set and prechecks precisely the surviving entries after browser reload or server workspace restart.
- request-AC5 -> This backlog slice. Proof: AC2: A trace-only subsequent load reuses the prechecked set without reopening the library; manual edits and uncheck-all survive reopening and refresh.
- request-AC6 -> This backlog slice. Proof: AC3: Same-name content stays distinct, missing entries are skipped, unique legacy names migrate safely, failures and unresolved imports preserve prior history, and purge clears history.

# Decision framing
- Product framing: Not needed
- Architecture framing: Not needed

# Links
- Product brief(s): `prod_015_optional_cursor_integration_and_reusable_dbc_import_defaults`
- Architecture decision(s): (none yet)
- Request: `req_032_add_opt_in_cursor_integral_analysis_and_restore_the_last_loaded_dbc_selection`
- Primary task(s): `task_047_deliver_opt_in_signal_integral_analysis_and_remembered_dbc_loading`

# Priority
- Priority: Medium
- Rationale: Set by scaffold input or defaulted for grooming.
