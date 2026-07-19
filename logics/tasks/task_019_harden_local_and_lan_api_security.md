## task_019_harden_local_and_lan_api_security - Harden local and LAN API security
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
- Sequence: 3 of 7; start after task 018 is complete.
- Commit only AC10-AC11 and their hostile tests/docs; do not include later slices.
- Suggested commit: `security(api): protect local and LAN access`.

# Backlog
- `item_019_harden_local_and_lan_api_security`

# Acceptance criteria
- AC10: L'API rejette un Host ou une Origin non autorises, exige un jeton de session
- AC11: L'import par chemin serveur est desactive hors boucle locale ou derriere une

# Validation
- Run Host, Origin, token, upload-limit and LAN path-import hostile tests.
- Run the full Python suite and `ruff check .`.
- Run `python3 -m logics_manager lint --require-status`.
- Use `python3 -m logics_manager flow progress task task_019_harden_local_and_lan_api_security.md --progress <n>%` during multi-wave work.
- Run `python3 -m logics_manager flow finish task task_019_harden_local_and_lan_api_security.md` after implementation.
- Finish workflow executed on 2026-07-18.
- Linked backlog/request close verification passed.

# Report
- Implementation complete.
- New `src/cantracediag/security.py` holds a `SecurityConfig` (resolved from env) and the
- Finished on 2026-07-18.
- Linked backlog item(s): `item_019_harden_local_and_lan_api_security`
- Related request(s): `req_007_finaliser_workflow_diagnostic_et_clarifier_cantracediag`
  Jupyter-style posture; `create_app` installs one HTTP middleware enforcing it and accepts
  an explicit `SecurityConfig` for tests.
- AC10 — Host/Origin/token/upload cap/no path leak: the middleware rejects a `Host` not on
  the loopback+configured allowlist (403) and a cross-site `Origin` (403); a per-process
  session token (embedded in the served shell via a `<meta name="ctd-token">`, sent by the
  UI as `X-CTD-Token`) is required on mutating endpoints locally and on every endpoint in
  LAN mode (401 otherwise). `/api/import-files` rejects oversized uploads by declared
  Content-Length and again while streaming (`_spool`, 413) using
  `CANTRACEDIAG_MAX_UPLOAD_MB`. `/api/import` error messages no longer echo the resolved
  local path. Hostile tests: `tests/test_security.py::test_disallowed_host_is_rejected`,
  `::test_cross_origin_request_is_rejected`, `::test_mutation_without_token_is_rejected_locally`,
  `::test_mutation_with_wrong_token_is_rejected`, `::test_read_endpoints_need_no_token_locally`,
  `::test_upload_over_limit_is_rejected`, `::test_missing_file_error_does_not_leak_paths`,
  `::test_index_embeds_session_token_locally`.
- AC11 — Server-path import gated: `/api/import` returns 403 unless `allow_server_import`,
  which defaults on for loopback and off in LAN (overridable via
  `CANTRACEDIAG_ALLOW_SERVER_IMPORT`). `--lan` binds `0.0.0.0`, allowlists the detected LAN
  IP, forces token-on-everything and disables server-path import, and prints the tokened
  URL. Tests: `::test_lan_mode_requires_token_on_reads`, `::test_lan_mode_disables_server_path_import`,
  `::test_lan_mode_index_requires_token`.
- Test harness: all authenticated clients go through `tests/conftest.py::make_client`
  (loopback Host + token); the E2E live-server fixture now sends the token on its import.
- Validation: `ruff check .` clean; full suite `112 passed, 11 skipped` (Chromium E2E) in an
  isolated `uv` environment.

# AI Context
- Summary: Implement harden local and lan api security.
- Keywords: task, implementation, backlog, runtime, python
- Use when: You need a bounded implementation task for a backlog item.
- Skip when: The work is still at the request or backlog shaping stage.

# Links
- Request: `req_007_finaliser_workflow_diagnostic_et_clarifier_cantracediag`
- Product brief(s): (none yet)
- Architecture decision(s): (none yet)

# AC Traceability
- request-AC10 -> task_019. Proof: Host/Origin allowlist, session token on mutations/LAN, upload cap, no path leak; tests/test_security.py::test_disallowed_host_is_rejected, ::test_cross_origin_request_is_rejected, ::test_mutation_without_token_is_rejected_locally, ::test_upload_over_limit_is_rejected, ::test_missing_file_error_does_not_leak_paths.
- request-AC11 -> task_019. Proof: server-path import disabled outside loopback / in LAN; tests/test_security.py::test_lan_mode_disables_server_path_import, ::test_lan_mode_requires_token_on_reads.
