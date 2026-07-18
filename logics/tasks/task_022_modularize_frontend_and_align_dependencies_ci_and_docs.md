## task_022_modularize_frontend_and_align_dependencies_ci_and_docs - Modularize frontend and align dependencies CI and docs
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
- Sequence: 6 of 7; start after task 021 is complete.
- Commit AC15-AC17 while preserving the existing UI hierarchy for task 023.
- Suggested commit: `refactor(web): modularize workspace foundations`.

# Backlog
- `item_022_modularize_frontend_and_align_dependencies_ci_and_docs`

# Acceptance criteria
- AC15: `app.js` et le CSS embarque sont decoupes par domaines `core`, `import`,
- AC16: `pyarrow` est utilise par l'export Parquet ou retire ; `python-can` est retire
- AC17: Le README, la roadmap, le backlog produit et les documents Logics ne

# Validation
- Run module loading/E2E surface checks, dependency checks and CI performance budgets.
- Run the complete Python and browser suites plus `ruff check .`.
- Run `python3 -m logics_manager lint --require-status`.
- Use `python3 -m logics_manager flow progress task task_022_modularize_frontend_and_align_dependencies_ci_and_docs.md --progress <n>%` during multi-wave work.
- Run `python3 -m logics_manager flow finish task task_022_modularize_frontend_and_align_dependencies_ci_and_docs.md` after implementation.

# Report
- Implementation complete.

# AI Context
- Summary: Implement modularize frontend and align dependencies ci and docs.
- Keywords: task, implementation, backlog, runtime, python
- Use when: You need a bounded implementation task for a backlog item.
- Skip when: The work is still at the request or backlog shaping stage.

# Links
- Request: `req_007_finaliser_workflow_diagnostic_et_clarifier_cantracediag`
- Product brief(s): (none yet)
- Architecture decision(s): (none yet)
