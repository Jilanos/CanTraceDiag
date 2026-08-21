## item_044_resolve_legacy_acceptance_criteria_traceability_and_lifecycle_debt - Resolve legacy acceptance-criteria traceability and lifecycle debt
> From version: 1.0.0
> Schema version: 1.0
> Status: Ready
> Understanding: 90%
> Confidence: 85%
> Progress: 0%
> Complexity: High
> Theme: Traceability remediation
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.
> Indicators reviewed: 2026-08-21 09:52:29

# AI Context
- Summary: Reconcile historical acceptance criteria with verifiable implementation evidence or managed retirement.
- Keywords: legacy requests, AC proof, successor chain
- Use when: An audit blocker concerns an unproven or obsolete acceptance criterion.
- Skip when: The finding is limited to authored diagram or metadata hygiene.

# Problem
- Several legacy requests block the audit because their acceptance criteria have no task-level proof, even though some work may have been delivered or superseded.
- Applying placeholder proof would conceal the distinction between verified delivery and obsolete planning.

# Scope
- In:
  - Build a finding-to-document inventory from the current audit output and classify each legacy acceptance criterion.
  - Use `flow repair ac-traceability` only with real commit and validation proof, then validate the repaired request.
  - Use managed withdraw, close, or successor links for work that is obsolete, duplicated, or never delivered.
  - Update active-task ownership and next-action signals through Logics Manager where they are stale or ambiguous.
- Out:
  - Inventing evidence, backdating validation, or changing source code to justify a documentation repair.
  - Resolving product companion diagrams or generic document-hygiene warnings outside the affected lifecycle documents.

# Acceptance criteria
- AC1: The audit inventory accounts for every initially blocking legacy request acceptance criterion.
- AC2: Each repaired proof identifies a real source commit and validation command, while each obsolete item has a valid managed successor or withdrawal transition.
- AC3: No active request or task remains duplicated or lacks a concrete CLI-visible next action.

# AC Traceability
- request-AC1 -> This backlog slice. Proof: AC1: The audit inventory accounts for every initially blocking legacy request acceptance criterion.
- request-AC2 -> This backlog slice. Proof: AC2: Each repaired proof identifies a real source commit and validation command, while each obsolete item has a valid managed successor or withdrawal transition.
- request-AC4 -> This backlog slice. Proof: AC3: No active request or task remains duplicated or lacks a concrete CLI-visible next action.

# Decision framing
- Product framing: Not needed
- Architecture framing: Not needed

# Links
- Product brief(s): `prod_011_reliable_logics_workflow_governance`
- Architecture decision(s): (none yet)
- Request: `req_024_restore_logics_workflow_integrity_and_audit_closure`
- Primary task(s): `task_043_deliver_clean_logics_workflow_audit_baseline`

# Priority
- Priority: High
- Rationale: Set by scaffold input or defaulted for grooming.
