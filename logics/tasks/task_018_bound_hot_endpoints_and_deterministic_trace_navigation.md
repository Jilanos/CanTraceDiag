## task_018_bound_hot_endpoints_and_deterministic_trace_navigation - Bound hot endpoints and deterministic trace navigation
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
- Sequence: 2 of 7; start after task 017 is complete.
- Commit only AC8-AC9 and their benchmarks/tests/docs; do not include later slices.
- Suggested commit: `perf(trace): bound cursor lookup and pagination`.

# Backlog
- `item_018_bound_hot_endpoints_and_deterministic_trace_navigation`

# Acceptance criteria
- AC8: La recherche du point le plus proche utilise au plus une requete bornee avant
- AC9: La trace est ordonnee par `(timestamp_s, seq)` et paginee par curseur opaque.

# Validation
- Run same-timestamp pagination, locate coherence and cursor plan/benchmark tests.
- Run the full Python suite and `ruff check .`.
- Run `python3 -m logics_manager lint --require-status`.
- Use `python3 -m logics_manager flow progress task task_018_bound_hot_endpoints_and_deterministic_trace_navigation.md --progress <n>%` during multi-wave work.
- Run `python3 -m logics_manager flow finish task task_018_bound_hot_endpoints_and_deterministic_trace_navigation.md` after implementation.
- Finish workflow executed on 2026-07-18.
- Linked backlog/request close verification passed.

# Report
- Implementation complete.
- AC8 — Bounded nearest lookups + batch endpoint: `TraceStore.nearest_sample` and
- Finished on 2026-07-18.
- Linked backlog item(s): `item_018_bound_hot_endpoints_and_deterministic_trace_navigation`
- Related request(s): `req_007_finaliser_workflow_diagnostic_et_clarifier_cantracediag`
  `nearest_frame_for_signal` now use one bounded `<=` and one bounded `>=` `LIMIT 1`
  query (via `TraceStore._nearest_rows`) and keep the closer, instead of sorting every
  row by absolute distance. New `POST /api/cursors` returns the nearest value of N
  signals at cursors A and B in a single call; the frontend readout (`refreshCursorReadout`
  in `web/app.js`) fires it once instead of 2N `/api/cursor` requests. Empirically DuckDB
  scans without a usable ART index for this shape, so the benchmark is a deterministic
  query-plan guard rather than a flaky wall-clock ratio:
  `tests/test_trace_nav.py::test_nearest_sample_plan_stays_two_bounded_queries` asserts the
  lookup stays exactly two bounded `LIMIT 1` queries (one `<=`, one `>=`), never an
  `abs()` distance sort, and that the query count does not grow with trace size.
  Correctness at edges/midpoints: `::test_nearest_sample_is_correct_at_edges_and_midpoints`.
  Batch endpoint: `::test_cursors_batch_endpoint_returns_a_and_b`,
  `::test_cursors_batch_omits_absent_cursor`.
- AC9 — Deterministic order + opaque cursor pagination: the import pipeline assigns one
  global `seq` across frames and events in file order (`src/cantracediag/pipeline.py`), so
  `(timestamp_s, seq)` is a gap-free total order even when frames and events share a
  timestamp. `TraceStore.trace_rows` paginates by opaque base64 keyset cursor
  (`_encode_cursor`/`_decode_cursor`/`_keyset_predicate`) instead of `OFFSET`, returning
  `start_index`, `next_cursor`, `prev_cursor`. `locate_row` returns an `at` cursor that
  opens the page starting exactly on the located row. Frontend pagination and locate now
  follow cursors (`web/app.js`). Proof on a same-timestamp fixture
  (`tests/fixtures/same_timestamp.asc`):
  `tests/test_trace_nav.py::test_same_timestamp_pagination_has_no_duplicate_or_omission`,
  `::test_same_timestamp_rows_are_totally_ordered_by_seq`,
  `::test_prev_cursor_round_trips_to_the_same_page`,
  `::test_locate_opens_page_starting_on_the_located_row`,
  `::test_locate_coherent_across_same_timestamp_rows`,
  `::test_trace_endpoint_rejects_malformed_cursor`; store contract updated in
  `tests/test_store_pipeline.py::test_trace_rows_pagination`.
- Validation: `ruff check .` clean; full suite `99 passed, 11 skipped` (Chromium E2E) in an
  isolated `uv` environment.

# AI Context
- Summary: Implement bound hot endpoints and deterministic trace navigation.
- Keywords: task, implementation, backlog, runtime, python
- Use when: You need a bounded implementation task for a backlog item.
- Skip when: The work is still at the request or backlog shaping stage.

# Links
- Request: `req_007_finaliser_workflow_diagnostic_et_clarifier_cantracediag`
- Product brief(s): (none yet)
- Architecture decision(s): (none yet)

# AC Traceability
- request-AC8 -> task_018. Proof: bounded nearest lookup (one `<=` + one `>=` LIMIT 1, no abs-sort) and a batch cursor endpoint; tests/test_trace_nav.py::test_nearest_sample_plan_stays_two_bounded_queries and ::test_cursors_batch_endpoint_returns_a_and_b.
- request-AC9 -> task_018. Proof: canonical (timestamp_s, seq) order with opaque keyset pagination; tests/test_trace_nav.py::test_same_timestamp_pagination_has_no_duplicate_or_omission and ::test_locate_opens_page_starting_on_the_located_row.
