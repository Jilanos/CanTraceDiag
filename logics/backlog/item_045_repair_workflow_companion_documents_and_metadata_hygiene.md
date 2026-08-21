## item_045_repair_workflow_companion_documents_and_metadata_hygiene - Repair workflow companion documents and metadata hygiene
> From version: 1.0.0
> Schema version: 1.0
> Status: In progress
> Understanding: 90%
> Confidence: 85%
> Progress: 10%
> Complexity: Medium
> Theme: Document hygiene
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.
> Indicators reviewed: 2026-08-21 09:56:52

# AI Context
- Summary: Repair authored companion content and metadata references after lifecycle evidence has been settled.
- Keywords: Mermaid overview, lineage declaration, code anchor
- Use when: Audit findings concern diagrams, stale links, or generated document wording.
- Skip when: A lifecycle decision or acceptance-criteria proof is still unresolved.

# Problem
- Missing product overview diagrams, stale code anchors, prose-only lineage, and generated AI-context wording prevent the corpus from communicating reliable scope and ownership.
- Some findings require authored content, while others require sanctioned deterministic repair commands.

# Scope
- In:
  - Author concise ASCII-safe Mermaid overview diagrams for product documents reported by audit.
  - Correct stale repository-relative code anchors, declared lineage links, and AI-context text using the appropriate document or Logics Manager mechanism.
  - Refresh Mermaid signatures and indicators after authored diagram or document changes.
  - Validate the touched documents with `flow validate` before proceeding to corpus-wide validation.
- Out:
  - Changing product requirements or implementation scope merely to simplify a diagram.
  - Adding diagrams to documents not reported by the audit without a demonstrated need.

# Acceptance criteria
- AC1: Every audit-reported missing companion diagram has a clear, valid overview Mermaid diagram with a refreshed signature.
- AC2: Workflow links and code anchors resolve to real repository documents or are removed as obsolete.
- AC3: AI-context sections describe document-specific execution context rather than template-generated wording.

# AC Traceability
- request-AC1 -> This backlog slice. Proof: AC1: Every audit-reported missing companion diagram has a clear, valid overview Mermaid diagram with a refreshed signature.
- request-AC3 -> This backlog slice. Proof: AC2: Workflow links and code anchors resolve to real repository documents or are removed as obsolete.

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
