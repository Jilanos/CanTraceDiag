## item_040_add_displayed_filtering_and_collapsible_ordered_dbc_groups_to_the_signal_explorer - Add displayed filtering and collapsible ordered DBC groups to the signal explorer
> From version: 1.0.0
> Schema version: 1.0
> Status: In progress
> Understanding: 90%
> Confidence: 85%
> Progress: 10%
> Complexity: Medium
> Theme: Signal explorer usability
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.
> Indicators reviewed: 2026-08-20 10:55:00

# AI Context
- Summary: (unfilled: replace before this doc is used)
- Keywords: add, displayed, filtering, collapsible, ordered, dbc, groups, signal, explorer
- Use when: (unfilled: replace before this doc is used)
- Skip when: (unfilled: replace before this doc is used)

# Problem
- The explorer renders all DBC groups expanded and alphabetically, making a large multi-DBC catalog difficult to scan.
- Operators cannot restrict the list to the signals already plotted.

# Scope
- In:
  - Expose enough ordered DBC metadata for the UI to identify the most recently used DBC of the loaded/restored analysis.
  - Add the displayed-only control beside favorites-only, persist its preference consistently with favorites-only, and combine its predicate with the existing search and favorites predicates.
  - Render all loaded DBCs as accessible expandable group headers, place the active DBC first, and default only non-active groups to collapsed.
  - Preserve independent expansion state without altering selected signals, favorites, or search text.
  - Add focused automated coverage for the filter and DBC group interactions.
- Out:
  - Changing decoder behavior, DBC parsing, or conflict resolution.
  - Removing signals from selected plots when their group is collapsed or filtered out.
  - Persisting sensitive DBC contents beyond the existing local workspace behavior.

# Acceptance criteria
- AC1: Displayed-only, favorites-only, and text filtering produce their intersection from the current catalog and selection.
- AC2: The last-used DBC is first and expanded after loading/restoring; each remaining loaded DBC is listed and collapsed by default.
- AC3: Each DBC header exposes its expanded state to keyboard and assistive-technology users, and toggling it affects only that group's rows.
- AC4: Tests demonstrate filter intersection, empty results, active-group ordering, and expand/collapse persistence through re-rendering.

# AC Traceability
- request-AC1 -> This backlog slice. Proof: AC1: Displayed-only, favorites-only, and text filtering produce their intersection from the current catalog and selection.
- request-AC2 -> This backlog slice. Proof: AC2: The last-used DBC is first and expanded after loading/restoring; each remaining loaded DBC is listed and collapsed by default.
- request-AC3 -> This backlog slice. Proof: AC3: Each DBC header exposes its expanded state to keyboard and assistive-technology users, and toggling it affects only that group's rows.
- request-AC5 -> This backlog slice. Proof: AC4: Tests demonstrate filter intersection, empty results, active-group ordering, and expand/collapse persistence through re-rendering.
- request-AC6 -> This backlog slice. Proof: AC4: Tests demonstrate filter intersection, empty results, active-group ordering, and expand/collapse persistence through re-rendering.

# Decision framing
- Product framing: Not needed
- Architecture framing: Not needed

# Links
- Product brief(s): `prod_008_compact_signal_exploration_for_cantracediag`
- Architecture decision(s): (none yet)
- Request: `req_021_make_the_signal_explorer_more_efficient_on_compact_screens`
- Primary task(s): `task_040_deliver_compact_signal_explorer_navigation_and_browser_fullscreen`

# Priority
- Priority: High
- Rationale: Set by scaffold input or defaulted for grooming.
