## prod_009_efficient_multi_dbc_signal_exploration - Efficient multi-DBC signal exploration
> Date: 2026-08-20
> Status: Proposed
> Related request: `req_022_streamline_navigation_of_large_multi_dbc_signal_catalogs`
> Related backlog: `item_042_prioritize_relevant_dbcs_and_add_message_level_signal_navigation`
> Related task: `task_041_deliver_concise_multi_dbc_explorer_navigation`
> Related architecture: (none yet)
> Reminder: Update status, linked refs, scope, decisions, success signals, and open questions when you edit this doc.

# Overview
Refine the signal explorer so large imported DBC catalogs prioritize live diagnostic relevance and remain fast to navigate during targeted signal searches.

# Goals
- Make used and active DBCs immediately useful while preserving access to the entire imported catalog.
- Turn a global signal search into a concise, result-oriented navigation surface.
- Provide message-level structure for dense DBCs without disrupting plots or saved explorer preferences.

# Non-goals
- Change DBC parsing, CAN decoding, conflict resolution, or trace storage.
- Remove an imported DBC or signal from the catalog because it is initially hidden.
- Replace the existing global search with a separate per-DBC search field.

# Scope and guardrails
- In: scaffolded request, product, backlog, orchestration task, validation, and handoff context.
- Out: unrelated workflow docs and implementation of generated tasks.

# Key product decisions
- Use structured input as the source of truth for generated docs.
- Keep generated write paths local and repo-bounded.

# Success signals
- Generated docs pass lint and audit without broad manual rewrites.
- Context-pack output can be handed to an implementation agent directly.

# References
- Product back-reference: `req_022_streamline_navigation_of_large_multi_dbc_signal_catalogs`
- Task back-reference: `task_041_deliver_concise_multi_dbc_explorer_navigation`
