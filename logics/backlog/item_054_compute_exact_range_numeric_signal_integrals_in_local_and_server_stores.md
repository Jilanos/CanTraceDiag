## item_054_compute_exact_range_numeric_signal_integrals_in_local_and_server_stores - Compute exact-range numeric signal integrals in local and server stores
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: Medium
> Theme: Numerical signal analysis
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.
> Indicators reviewed: 2026-09-30 13:57:06

# AI Context
Calculate from stored decoded physical values with boundary neighbors. The canvas draws steps, but this feature deliberately reports trapezoidal interpolation; never reuse the decimated plot samples.

# Problem
- Existing range statistics do not expose an integral; plot decimation cannot be used for trustworthy area computation.
- Cursor timestamps may fall between samples or outside signal coverage.

# Scope
- In:
  - Priority rationale: add requested analysis after existing High priority correctness work; this slice enables the opt-in UI.
  - Use signed numerical trapezoidal integration of decoded physical values over [min(A,B), max(A,B)] with timestamps in seconds; swapping cursor labels preserves the result and negative values subtract area. This explicitly uses piecewise linear interpolation even though the existing plot draws sample-and-hold steps; identify the method in the enabled analysis UI.
  - Use full-resolution stored samples, never the downsampled /api/series plot arrays. Retrieve at most the adjacent bracketing samples outside the interval to interpolate exact cursor boundaries; never extrapolate beyond available signal data.
  - For positive duration require finite numeric coverage at both boundaries and at least two distinct timestamps. Return a structured unavailable reason for missing coverage, text-only signals, or invalid/non-finite segments; do not silently bridge explicit invalid samples. Irregular finite sampling is interpolated without inventing a gap threshold.
  - Collapse duplicate timestamps deterministically to the last sample in stable ingestion order before interpolation. A zero-width interval with a defined finite value returns 0; otherwise it is unavailable.
  - Return interval bounds, method, integral, and unit metadata; show DBC-unit multiplied by seconds (for example A·s), or s for a dimensionless signal. Do not silently convert A·s into Ah or other derived units.
  - Analytical fixtures: constant 2 on [1,4] gives 6; linear v(t)=t on [0.5,2.5] gives 3; values -2 at t=0 and 2 at t=2 give 0. Cover reversed cursors, equal cursors, irregular spacing, duplicate timestamps, interpolated boundaries, missing boundaries, non-finite values, and text signals with Python/TypeScript parity.
  - Expose an explicit integral operation through the server API and local adapter with input validation and existing signal identity semantics. Query only the target signal/range plus boundary neighbors; no full-trace payload to the browser.
- Out:
  - Changing default range statistics, plot interpolation, decoding, or unit conversion.

# Acceptance criteria
- AC1: Full-resolution signed trapezoidal output matches the constant, ramp, and sign-changing analytical fixtures and is invariant under zoom, decimation, and swapped cursor labels.
- AC2: Both engines implement exact boundary interpolation, stable duplicate handling, zero-width semantics, and explicit unavailable results without extrapolation or invalid-data bridging.
- AC3: API/adapter output contains value, unit, method, bounds, and unavailable reason as applicable; equivalent fixtures produce equivalent Python and TypeScript results.

# AC Traceability
- request-AC3 -> This backlog slice. Proof: AC1: Full-resolution signed trapezoidal output matches the constant, ramp, and sign-changing analytical fixtures and is invariant under zoom, decimation, and swapped cursor labels.
- request-AC6 -> This backlog slice. Proof: AC2: Both engines implement exact boundary interpolation, stable duplicate handling, zero-width semantics, and explicit unavailable results without extrapolation or invalid-data bridging.

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

# Tasks
- `task_047_deliver_opt_in_signal_integral_analysis_and_remembered_dbc_loading`

# Notes
- Task `task_047_deliver_opt_in_signal_integral_analysis_and_remembered_dbc_loading` was finished via `logics-manager flow finish task` on 2026-09-30.
