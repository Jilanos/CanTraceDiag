## task_018_bound_hot_endpoints_and_deterministic_trace_navigation - Bound hot endpoints and deterministic trace navigation
> From version: 0.1.0
> Schema version: 1.0
> Status: Ready
> Understanding: 90%
> Confidence: 85%
> Progress: 0%
> Complexity: Medium
> Theme: Implementation delivery
> Reminder: Update status/understanding/confidence/progress and linked request/backlog references when you edit this doc.

# Definition of Done (DoD)
- [ ] The backlog scope is implemented.
- [ ] Acceptance criteria are covered.
- [ ] Validation passes.
- [ ] Implementation, tests and documentation are delivered together in one dedicated commit for this task.

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

# Report
- Implementation complete.

# AI Context
- Summary: Implement bound hot endpoints and deterministic trace navigation.
- Keywords: task, implementation, backlog, runtime, python
- Use when: You need a bounded implementation task for a backlog item.
- Skip when: The work is still at the request or backlog shaping stage.

# Links
- Request: `req_007_finaliser_workflow_diagnostic_et_clarifier_cantracediag`
- Product brief(s): (none yet)
- Architecture decision(s): (none yet)
