## item_042_prioritize_relevant_dbcs_and_add_message_level_signal_navigation - Prioritize relevant DBCs and add message-level signal navigation
> From version: 1.0.0
> Schema version: 1.0
> Status: Ready
> Understanding: 90%
> Confidence: 85%
> Progress: 0%
> Complexity: Medium
> Theme: Signal explorer usability
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# AI Context
- Summary: (unfilled: replace before this doc is used)
- Keywords: prioritize, relevant, dbcs, add, message, level, signal, navigation
- Use when: (unfilled: replace before this doc is used)
- Skip when: (unfilled: replace before this doc is used)

# Problem
- A catalog with many imported DBCs becomes a visually repetitive stack of headers, even when most files have no signal used by the trace.
- A dense DBC forces operators to scan a long flat list after finding the relevant database.

# Scope
- In:
  - Define a default relevant-DBC view containing the active DBC and DBCs represented in the loaded trace, plus a compact explicit control for unused imported DBCs.
  - Make global search remove empty DBC and message sections and display match counts for visible DBCs.
  - Group each DBC's signal rows by CAN message with independent accessible expansion state.
  - Preserve selected signals, favorites, query text, DBC expansion state, and existing shown-only behavior through all hierarchy changes.
  - Align the server-backed UI and local PWA data contracts and add browser-focused tests for multi-DBC sessions.
- Out:
  - Changing the underlying signal catalog, decoder output, or DBC conflict policy.
  - Removing unused DBCs from the import session or persisted local library.
  - Adding separate search fields for each DBC or message.

# Acceptance criteria
- AC1: In a session with six or more imported DBCs, the default view shows the active and trace-used DBCs first and exposes the remaining DBCs via one compact discoverable control.
- AC2: A global query displays only DBC and message sections with matching signals and each visible DBC reports its current match count.
- AC3: Message headers are keyboard-operable, expose expanded state, and toggle only their own signal rows.
- AC4: Selecting, plotting, favoriting, filtering, or reopening sections does not lose user state or hide a selected signal from the shown-only filter.
- AC5: Automated server UI and local PWA coverage demonstrates six-DBC behavior, search narrowing, message expansion, and supported viewport accessibility.

# AC Traceability
- request-AC1 -> This backlog slice. Proof: AC1: In a session with six or more imported DBCs, the default view shows the active and trace-used DBCs first and exposes the remaining DBCs via one compact discoverable control.
- request-AC2 -> This backlog slice. Proof: AC2: A global query displays only DBC and message sections with matching signals and each visible DBC reports its current match count.
- request-AC3 -> This backlog slice. Proof: AC3: Message headers are keyboard-operable, expose expanded state, and toggle only their own signal rows.
- request-AC4 -> This backlog slice. Proof: AC4: Selecting, plotting, favoriting, filtering, or reopening sections does not lose user state or hide a selected signal from the shown-only filter.
- request-AC5 -> This backlog slice. Proof: AC5: Automated server UI and local PWA coverage demonstrates six-DBC behavior, search narrowing, message expansion, and supported viewport accessibility.

# Decision framing
- Product framing: Not needed
- Architecture framing: Not needed

# Links
- Product brief(s): `prod_009_efficient_multi_dbc_signal_exploration`
- Architecture decision(s): (none yet)
- Request: `req_022_streamline_navigation_of_large_multi_dbc_signal_catalogs`
- Primary task(s): `task_041_deliver_concise_multi_dbc_explorer_navigation`

# Priority
- Priority: High
- Rationale: Set by scaffold input or defaulted for grooming.
