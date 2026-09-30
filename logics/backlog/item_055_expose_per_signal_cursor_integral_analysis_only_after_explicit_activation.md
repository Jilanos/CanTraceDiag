## item_055_expose_per_signal_cursor_integral_analysis_only_after_explicit_activation - Expose per-signal cursor integral analysis only after explicit activation
> From version: 1.0.0
> Schema version: 1.0
> Status: In progress
> Understanding: 90%
> Confidence: 85%
> Progress: 30%
> Complexity: Medium
> Theme: Optional analysis UI
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.
> Indicators reviewed: 2026-09-30 13:04:12

# AI Context
Integral mode belongs to one chosen signal in the current trace. Gate both rendering and backend work, and invalidate pending responses whenever activation, target, or trace changes.

# Problem
- An always-visible integral column would add clutter and violate the requested opt-in behavior.

# Scope
- In:
  - Priority rationale: requested optional diagnostic capability; implement after the numeric integral contract.
  - Add a compact keyboard-operable integral action and a single target selected-signal choice; activation is explicit and independent of existing range statistics.
  - Store enabled/target state only in the current trace analysis; reset on new trace, purge, and reload. Removing the target signal disables integral mode until another explicit activation.
  - Create integral result UI only while enabled, identify trapezoidal interpolation and unit, and handle absent cursors or unavailable numeric coverage.
  - Recompute for target/cursor changes using existing debounce patterns and reject stale async responses after newer requests, disable, or trace replacement. Zero integral computation or requests while disabled; do not fan out across all selected signals.
  - Add browser checks for default absence, activation, target switch, movement, disable, reset, stale responses, keyboard operation, and existing cursor dragging/statistics.
- Out:
  - Persistent opt-in preferences, always-visible result columns, integral plots, and automatic activation.

# Acceptance criteria
- AC1: Fresh and newly imported traces show no integral result or integral-specific work; an accessible explicit action enables analysis for one signal.
- AC2: Enabled results follow current signal and cursor bounds, expose units/method and unavailable reasons, and cannot be overwritten by stale responses.
- AC3: Disabling, removing the target, changing trace, or purging removes the result and stops integral work; regression coverage preserves ordinary cursor statistics and dragging.

# AC Traceability
- request-AC1 -> This backlog slice. Proof: AC1: Fresh and newly imported traces show no integral result or integral-specific work; an accessible explicit action enables analysis for one signal.
- request-AC2 -> This backlog slice. Proof: AC2: Enabled results follow current signal and cursor bounds, expose units/method and unavailable reasons, and cannot be overwritten by stale responses.
- request-AC6 -> This backlog slice. Proof: AC3: Disabling, removing the target, changing trace, or purging removes the result and stops integral work; regression coverage preserves ordinary cursor statistics and dragging.

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
