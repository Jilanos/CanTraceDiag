## prod_014_reliable_binary_blf_can_trace_import - Reliable binary BLF CAN trace import
> Date: 2026-08-28
> Status: Settled
> Related request: `req_031_import_binary_blf_can_trace_recordings`
> Related backlog: `item_053_add_bounded_vector_blf_import_with_diagnostics_and_explicit_pwa_capability`
> Related task: `task_046_deliver_reliable_binary_blf_trace_import`
> Related architecture: (none yet)
> Reminder: Update status, linked refs, scope, decisions, success signals, and open questions when you edit this doc.
> Indicators reviewed: 2026-08-28 10:56:24

# Overview
Extend the diagnostic workstation with a bounded, safe Vector BLF import path while preserving the existing normalized CAN model and established ASC/TRC workflows.

```mermaid
flowchart LR
  A[BLF input] --> B[Defensive import adapter]
  B --> C[Normalized CAN model]
  C --> D[Diagnostic workflows]
```

# Goals
- Make a documented classic-CAN subset of binary BLF recordings a first-class server-backed trace input.
- Preserve integrity, ordering, diagnostics, and bounded-memory behavior for large binary recordings.
- Make the static-PWA BLF support boundary deliberate, visible, and testable rather than advertising unsupported binary import.

# Non-goals
- Implement MF4, PCAP, replay, or automatic conversion through external desktop tools.
- Promise support for every BLF object type, CAN FD, CAN XL, LIN, FlexRay, or other bus protocols in this delivery.
- Change ASC/TRC parsing semantics, DBC conflict handling, report schemas, or export schemas.

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
- Product back-reference: `item_053_add_bounded_vector_blf_import_with_diagnostics_and_explicit_pwa_capability`
- Task back-reference: `task_046_deliver_reliable_binary_blf_trace_import`
