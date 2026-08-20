## req_021_make_the_signal_explorer_more_efficient_on_compact_screens - Make the signal explorer more efficient on compact screens
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Complexity: Medium
> Theme: Signal explorer usability
> Reminder: Update status/understanding/confidence and linked backlog/task references when you edit this doc.
> Indicators reviewed: 2026-08-20 11:09:10

# AI Context
- Summary: (unfilled: replace before this doc is used)
- Keywords: signal, explorer, more, efficient, compact, screens
- Use when: (unfilled: replace before this doc is used)
- Skip when: (unfilled: replace before this doc is used)

# Needs
- Filter the signal explorer to signals currently displayed as plots, alongside the existing favorites filter.
- Make DBC groups in the signal explorer compact and navigable, with the active DBC prominent and all other imported DBCs available on demand.
- Let operators enter and leave browser fullscreen from the application to recover space on small screens.

# Context
- The current explorer groups catalog entries by the first database name, lists groups alphabetically, and renders every group expanded.
- Selection is the canonical source for plotted signals in `state.selected`; favorites and selected signals are persisted in browser storage.
- An imported/restored analysis already exposes the ordered DBC paths in the server session, but `/api/signals` currently returns only the catalog entries.
- The requested active DBC is the DBC most recently used by the loaded or restored analysis. It is displayed first and starts expanded; all other loaded DBC groups remain visible as collapsed headers with an arrow control.
- The active DBC group itself is collapsible. Expanding or collapsing a group must not change signal selection, favorites, the search text, or the other filter state.
- The displayed-only and favorites-only filters combine with the existing text search using AND semantics. Displayed means a signal is currently selected for plotting, including a selected signal whose source DBC group is collapsed.
- The Web Fullscreen API can only be requested from a user gesture and cannot programmatically invoke the browser's F11 chrome-hiding mode. The UI must therefore request document fullscreen, reflect native fullscreen changes, and remain usable when the request is denied or unsupported.
- The web UI is keyboard-accessible and its current end-to-end suite uses Playwright. Tests must cover keyboard and assistive-technology semantics as well as visual state changes.

# Acceptance criteria
- AC1: The Signals header provides an accessible displayed-only checkbox next to the existing favorites-only control; when enabled, the list contains only currently plotted signals and combines predictably with text search and favorites-only filtering.
- AC2: The active DBC is first and initially expanded. Every loaded DBC, including DBCs without a currently matching signal, has a visible, keyboard-operable expandable header; non-active DBC groups start collapsed and the active group can also be collapsed.
- AC3: Collapsing, expanding, filtering, selecting, or unselecting signals preserves selected signals, favorite signals, the text query, and unrelated DBC group state. The explorer has a clear empty state when filters match no signal.
- AC4: An accessible fullscreen control requests and exits document fullscreen from a user action, accurately updates its pressed/label state after browser fullscreen changes, and presents a non-disruptive failure state when fullscreen is unavailable or denied. Escape exits fullscreen according to browser behavior.
- AC5: The updated explorer and fullscreen control remain operable at the supported desktop and 390x844 small-screen viewports, without horizontal overflow or inaccessible controls.
- AC6: Focused unit or browser tests cover displayed-only filtering, DBC group ordering and expansion, and fullscreen success, exit, and failure paths.

# Definition of Ready (DoR)
- [x] Problem statement is explicit and user impact is clear.
- [x] Scope boundaries (in/out) are explicit.
- [x] Acceptance criteria are testable.
- [x] Dependencies and known risks are listed.

# Companion docs
- Product brief(s): `prod_008_compact_signal_exploration_for_cantracediag`
- Architecture decision(s): (none yet)

# References
- src/cantracediag/web/index.html
- src/cantracediag/web/js/signals.js
- src/cantracediag/web/js/main.js
- src/cantracediag/web/styles.css
- tests/test_e2e_ui.py

# Backlog
- `item_040_add_displayed_filtering_and_collapsible_ordered_dbc_groups_to_the_signal_explorer`
- `item_041_add_a_resilient_browser_fullscreen_control_for_the_diagnostic_workspace`
