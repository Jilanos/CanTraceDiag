## req_022_streamline_navigation_of_large_multi_dbc_signal_catalogs - Streamline navigation of large multi-DBC signal catalogs
> From version: 1.0.0
> Schema version: 1.0
> Status: Draft
> Understanding: 95%
> Confidence: 90%
> Complexity: Medium
> Theme: Signal explorer usability
> Reminder: Update status/understanding/confidence and linked backlog/task references when you edit this doc.

# AI Context
- Summary: (unfilled: replace before this doc is used)
- Keywords: streamline, navigation, large, multi, dbc, signal, catalogs
- Use when: (unfilled: replace before this doc is used)
- Skip when: (unfilled: replace before this doc is used)

# Needs
- Reduce the visual weight of a signal explorer containing many imported DBC files.
- Make the relevant DBCs and signal matches easy to find without losing access to the full catalog.
- Make dense DBC signal lists scannable through a second, message-level navigation layer.

# Context
- The current explorer renders one independently collapsible group per imported DBC and keeps the active DBC first.
- Real diagnostic sessions may contain many DBCs, including files with no decoded signal in the loaded trace, which makes a long stack of group headers visually heavy.
- Text search, favorites-only, and shown-only filtering already intersect in the explorer and selected signals remain visible as plot state.
- The deployed product is the local PWA, whose local backend must expose the same explorer metadata contract as the server UI.
- The existing explorer uses accessible buttons and aria-expanded state; new hierarchy controls must preserve keyboard and assistive-technology operation.
- This functional delivery must follow the project release policy: validate locally, commit implementation work, prepare and commit the next SemVer version, push, wait for CI on that exact version-preparation commit, then create and push one annotated version tag and verify the tag-triggered release workflow.

# Acceptance criteria
- AC1: The default explorer view prioritizes the active DBC and DBCs used by the current trace, while keeping unused imported DBCs discoverable through one compact on-demand control.
- AC2: A global text query hides DBC and message groups with no matches and shows an accurate match count for each remaining DBC group.
- AC3: Within a dense DBC, signals are grouped by CAN message in independently expandable, keyboard-operable message sections without changing signal selection, favorites, or the current query.
- AC4: The explorer remains compact and usable with at least six imported DBCs, including narrow desktop and mobile-supported viewports, without horizontal overflow.
- AC5: Server UI and local PWA keep equivalent DBC ordering, visibility, search, and message-group behavior, with automated coverage for the new defaults and interactions.

# Definition of Ready (DoR)
- [x] Problem statement is explicit and user impact is clear.
- [x] Scope boundaries (in/out) are explicit.
- [x] Acceptance criteria are testable.
- [x] Dependencies and known risks are listed.

# Companion docs
- Product brief(s): `prod_009_efficient_multi_dbc_signal_exploration`
- Architecture decision(s): (none yet)

# References
- logics/product/prod_008_compact_signal_exploration_for_cantracediag.md
- src/cantracediag/web/js/signals.js
- src/cantracediag/web/styles.css
- spikes/pwa-local-engine/src/local-backend.ts
- spikes/pwa-local-engine/browser-smoke.mjs
- tests/test_e2e_ui.py

# Backlog
- `item_042_prioritize_relevant_dbcs_and_add_message_level_signal_navigation`
