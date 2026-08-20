## prod_010_interoperable_classic_can_trace_import - Interoperable classic CAN trace import
> Date: 2026-08-20
> Status: Proposed
> Related request: `req_023_import_text_trc_can_trace_recordings`
> Related backlog: `item_043_add_verified_text_trc_import_with_server_and_local_pwa_parity`
> Related task: `task_042_deliver_verified_text_trc_trace_import`
> Related architecture: (none yet)
> Reminder: Update status, linked refs, scope, decisions, success signals, and open questions when you edit this doc.

# Overview
Extend the diagnostic workstation with direct ingestion of a documented text .trc trace family while preserving its established ASC workflow and one normalized CAN data model.

# Goals
- Make supported classic-CAN .trc recordings first-class import inputs in both product surfaces.
- Retain data integrity and diagnostic visibility for records that cannot be decoded as classic CAN frames.
- Keep the import extension small, testable, and independent from DBC decoding and trace storage.

# Non-goals
- Implement CAN FD or CAN XL decoding, payloads beyond eight bytes, or a new database format.
- Support binary trace formats or every historical variation of the .trc extension in this delivery.
- Alter existing ASC parsing semantics, DBC conflict handling, chart behavior, or export schemas.

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
- Product back-reference: `req_023_import_text_trc_can_trace_recordings`
- Task back-reference: `task_042_deliver_verified_text_trc_trace_import`
