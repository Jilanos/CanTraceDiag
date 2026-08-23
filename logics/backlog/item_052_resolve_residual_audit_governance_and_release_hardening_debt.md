## item_052_resolve_residual_audit_governance_and_release_hardening_debt - Resolve residual audit governance and release-hardening debt
> From version: 1.0.0
> Schema version: 1.0
> Status: In progress
> Understanding: 90%
> Confidence: 85%
> Progress: 10%
> Complexity: Medium
> Theme: Release governance
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.
> Indicators reviewed: 2026-08-23 09:50:36

# AI Context
- Summary: Triage the non-P0 audit findings into concrete fixes, lifecycle moves, follow-up docs, or explicit deferrals.
- Keywords: resolve, residual, audit, governance, release, hardening, debt
- Use when: Handling stale Logics records, fragile PWA assembly follow-ups, pinning policy, release parity, or the Starlette deprecation.
- Skip when: Implementing the immediate fullscreen or Docker-context slices.

# Problem
- The audit found several lower-priority risks that should not be mixed into the P0 fix but should not remain implicit.
- Production code under `spikes/`, text-marker rewriting, stale Logics records, mutable pins, and the Starlette deprecation each need a recorded disposition.

# Scope
- In:
  - Review the stale Logics chains named by `logics-manager health` and either close, obsolete, or split them using Logics lifecycle commands with evidence.
  - Create or update scoped follow-up work for replacing fragile PWA text rewrites and promoting the production PWA out of `spikes/`, unless that work is already covered by an active chain.
  - Harmonize the release-validation checklist with CI where appropriate and record any intentionally deferred checks with rationale.
  - Plan or implement the smallest safe step for supply-chain pinning consistency, starting with release workflow and Docker image mutability.
  - Plan or implement the Starlette/httpx test-client deprecation fix if it is still present when this slice starts.
- Out:
  - Large-scale frontend architecture migration without a dedicated implementation task.
  - Forced closeout of workflow documents that lack evidence.
  - Project-wide dependency upgrades not needed for release validation, pinning policy, or the test-client deprecation.

# Acceptance criteria
- AC1: Each residual audit item C3, C4, C5, C7, and C8 has a concrete outcome: fixed, linked to existing work, split into new work, or explicitly deferred with rationale.
- AC2: Logics lifecycle changes are made through `logics-manager flow` commands and pass lint and audit afterward.
- AC3: Any supply-chain or dependency changes include focused validation and do not weaken current CI or release gates.
- AC4: The task closeout records the final disposition table and links to any follow-up docs created.

# AC Traceability
- request-AC5 -> This backlog slice. Proof: AC1: Each residual audit item C3, C4, C5, C7, and C8 has a concrete outcome: fixed, linked to existing work, split into new work, or explicitly deferred with rationale.
- request-AC6 -> This backlog slice. Proof: AC2: Logics lifecycle changes are made through `logics-manager flow` commands and pass lint and audit afterward.

# Decision framing
- Product framing: Not needed
- Architecture framing: Not needed

# Links
- Product brief(s): `prod_013_reliable_static_pwa_delivery`
- Architecture decision(s): (none yet)
- Request: `req_028_harden_static_pwa_delivery_and_release_validation`
- Primary task(s): `task_045_deliver_static_pwa_delivery_and_release_hardening`

# Priority
- Priority: Medium
- Rationale: Set by scaffold input or defaulted for grooming.
