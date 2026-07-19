## task_020_enforce_asc_parsing_integrity - Enforce ASC parsing integrity
> From version: 0.1.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: Medium
> Theme: Implementation delivery
> Reminder: Update status/understanding/confidence/progress and linked request/backlog references when you edit this doc.
> Non-semantic edit: task-level AC traceability closure (req_007 AC17).

# Definition of Done (DoD)
- [x] The backlog scope is implemented.
- [x] Acceptance criteria are covered.
- [x] Validation passes.
- [x] Implementation, tests and documentation are delivered together in one dedicated commit for this task.

# Delivery order and commit boundary
- Sequence: 4 of 7; start after task 019 is complete.
- Commit only AC12 and its fixtures/tests/docs; do not include later slices.
- Suggested commit: `fix(asc): preserve and report malformed trace lines`.

# Backlog
- `item_020_enforce_asc_parsing_integrity`

# Acceptance criteria
- AC12: Une ligne ASC horodatee mais tronquee, un payload plus court ou plus long que

# Validation
- Run negative/scientific timestamp and malformed DLC/payload parser tests.
- Run the full Python suite and `ruff check .`.
- Run `python3 -m logics_manager lint --require-status`.
- Use `python3 -m logics_manager flow progress task task_020_enforce_asc_parsing_integrity.md --progress <n>%` during multi-wave work.
- Run `python3 -m logics_manager flow finish task task_020_enforce_asc_parsing_integrity.md` after implementation.
- Finish workflow executed on 2026-07-18.
- Linked backlog/request close verification passed.

# Report
- Implementation complete.
- AC12 — ASC parsing integrity: `src/cantracediag/formats/asc.py` now recognises a
- Finished on 2026-07-18.
- Linked backlog item(s): `item_020_enforce_asc_parsing_integrity`
- Related request(s): `req_007_finaliser_workflow_diagnostic_et_clarifier_cantracediag`
  data-frame line by its Rx/Tx direction and, instead of silently dropping or truncating
  a malformed one, emits an explicit `AscAnomaly` non-data event (visible in the trace and
  grouped under the report's ASC anomalies) with a specific reason for each defect:
  truncated data-frame line, payload shorter/longer than the DLC, data byte out of range
  0..255, and classic CAN DLC greater than 8. Trailing `Length =/BitCount =` metadata is
  still ignored (leading numeric tokens are the payload). The timestamp regex accepts
  negative and scientific-notation timestamps. No malformed line ever becomes a corrupt
  frame. Tests on a new `tests/fixtures/malformed.asc`:
  `tests/test_asc.py::test_negative_and_scientific_timestamps_are_accepted`,
  `::test_malformed_lines_become_explicit_anomalies_not_corrupt_frames`,
  `::test_valid_frames_survive_alongside_anomalies`; the decimal-base metadata fixture
  still passes.
- Validation: `ruff check .` clean; full suite `115 passed, 11 skipped` (Chromium E2E) in
  an isolated `uv` environment.

# AI Context
- Summary: Implement enforce asc parsing integrity.
- Keywords: task, implementation, backlog, runtime, python
- Use when: You need a bounded implementation task for a backlog item.
- Skip when: The work is still at the request or backlog shaping stage.

# Links
- Request: `req_007_finaliser_workflow_diagnostic_et_clarifier_cantracediag`
- Product brief(s): (none yet)
- Architecture decision(s): (none yet)

# AC Traceability
- request-AC12 -> task_020. Proof: malformed ASC lines become explicit AscAnomaly events, no corrupt frame; negative/scientific timestamps accepted; tests/test_asc.py::test_malformed_lines_become_explicit_anomalies_not_corrupt_frames, ::test_negative_and_scientific_timestamps_are_accepted.
