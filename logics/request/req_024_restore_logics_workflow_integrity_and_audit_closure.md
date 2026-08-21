## req_024_restore_logics_workflow_integrity_and_audit_closure - Restore Logics workflow integrity and audit closure
> From version: 1.0.0
> Schema version: 1.0
> Status: Draft
> Understanding: 90%
> Confidence: 85%
> Complexity: High
> Theme: Workflow integrity
> Reminder: Update status/understanding/confidence and linked backlog/task references when you edit this doc.
> Indicators reviewed: 2026-08-21 09:52:29

# AI Context
- Summary: Classify historic audit blockers before choosing evidence repair, lifecycle withdrawal, or successor linkage.
- Keywords: audit inventory, evidence integrity, lifecycle remediation
- Use when: Planning the document-only recovery of the Logics corpus.
- Skip when: Delivering application code or changing release infrastructure.

# Needs
- Make the Logics workflow auditable by resolving each current blocking finding through evidence, a valid lifecycle transition, or a documented replacement chain.
- Remove stale workflow metadata that makes an active, ready, or completed document misleading to the next implementer.
- Leave a repeatable audit baseline so later feature work can be closed without inheriting historical workflow debt.

# Context
- The current audit reports 50 blocking findings, primarily missing task-level acceptance-criteria traceability on legacy requests, plus missing companion Mermaid diagrams and document-hygiene warnings.
- Historical documents must not receive invented implementation proof: traceability must refer to an existing validated task, or the obsolete request must be withdrawn or superseded through the Logics CLI.
- The existing governance task includes release security work; this request is limited to workflow-document integrity and audit closure, and must not alter product behavior, release artifacts, or CI configuration.
- All lifecycle changes, indicators, links, and Mermaid signatures must be made through the sanctioned Logics Manager commands rather than manual metadata edits.
- The cleanup should be delivered in bounded waves so each category can be validated independently before the final corpus-wide audit.

# Acceptance criteria
- AC1: Every blocking audit finding present at the start of this work is inventoried and assigned to one of: deterministic repair, evidence-backed traceability repair, valid lifecycle transition, or an explicitly linked replacement document.
- AC2: Legacy requests with missing task-level acceptance-criteria proof either gain accurate proof tied to an existing implementation commit and validation, or are withdrawn/superseded without fabricated evidence.
- AC3: Required product companion diagrams, workflow links, indicators, AI-context wording, and code anchors are corrected using the appropriate managed or authored workflow mechanism.
- AC4: The active workflow set has one unambiguous next action per active task; duplicate or obsolete paths are closed, withdrawn, or linked to their successor through the CLI.
- AC5: `logics-manager lint --require-status` and `logics-manager audit --group-by-doc` pass at closeout, with validation evidence recorded in each completed cleanup task.

# Definition of Ready (DoR)
- [x] Problem statement is explicit and user impact is clear.
- [x] Scope boundaries (in/out) are explicit.
- [x] Acceptance criteria are testable.
- [x] Dependencies and known risks are listed.

# Companion docs
- Product brief(s): `prod_011_reliable_logics_workflow_governance`
- Architecture decision(s): (none yet)

# References
- logics/instructions.md
- logics/release/contract.json
- logics/request/req_004_optimiser_le_chargement_des_grosses_traces_par_decodage_a_la_demande.md
- logics/request/req_005_refonte_identite_ui_instrument_de_mesure.md
- logics/request/req_006_workspace_local_lancement_1_clic_bibliotheque_dbc_et_reprise_de_session.md
- logics/request/req_008_corriger_la_regression_ui_liee_au_cache_d_assets_statiques.md
- logics/request/req_012_rattraper_commits_ui_diagnostic_18_19_juillet_pwa.md
- logics/product/prod_007_identite_cantracediag_alignee_sur_icones_v3_corrige.md
- logics/product/prod_009_efficient_multi_dbc_signal_exploration.md

# Backlog
- `item_044_resolve_legacy_acceptance_criteria_traceability_and_lifecycle_debt`
- `item_045_repair_workflow_companion_documents_and_metadata_hygiene`
- `item_046_establish_a_repeatable_clean_audit_workflow_baseline`
