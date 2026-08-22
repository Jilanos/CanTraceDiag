## item_047_preserve_exact_anomaly_counts_in_browser_local_reports - Preserve exact anomaly counts in browser-local reports
> From version: 1.0.0
> Schema version: 1.0
> Status: Ready
> Understanding: 90%
> Confidence: 85%
> Progress: 0%
> Complexity: Low
> Theme: Diagnostic report correctness
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.
> Indicators reviewed: 2026-08-22 12:22:26

# AI Context
- Summary: Separate unique event-type discovery from exact event counting so browser-local reports preserve anomaly multiplicities.
- Keywords: preserve, exact, anomaly, counts, browser, local, reports
- Use when: Changing LocalTraceStore or LocalPwaBackend report contracts and their focused PWA regression tests.
- Skip when: Changing parser event classification, report design, DBC storage, or large-trace performance.

# Problem
- LocalTraceStore exposes event_types as a deduplicated list, and LocalPwaBackend.report increments each listed type once, so repeated anomalies are under-reported.
- The existing fixture contains only one event of each type and the tests assert report frames and paths but not anomaly multiplicities.

# Scope
- In:
  - Introduce an exact event-type count contract in the local store or report path while retaining the unique event-type list used by filters.
  - Align the browser-local report payload with the Python reference shape for anomaly counts.
  - Add a deterministic unit fixture containing repeated events of one type and mixed event types.
  - Assert backend payload counts and rendered report multiplicities, then run the standard PWA and Python non-regression suites.
- Out:
  - Changing event classification or parser behavior.
  - Redesigning report presentation or adding new anomaly categories.
  - Large-trace performance changes unrelated to event counting.

# Acceptance criteria
- AC1: A fixture with two ErrorFrame events and one Status event produces events equal to three, anomalies.asc_events.ErrorFrame equal to two, and anomalies.asc_events.Status equal to one.
- AC2: The event filter still lists ErrorFrame and Status once each, proving that unique filter values and counted report values remain separate contracts.
- AC3: The PWA report rendering shows ErrorFrame x2 and Status x1 from the backend payload without recomputing or losing counts.
- AC4: Focused Node tests fail against the reviewed implementation and pass after the correction; existing Python, Node, build, and browser-smoke validations remain green.

# AC Traceability
- request-AC1 -> This backlog slice. Proof: AC1: A fixture with two ErrorFrame events and one Status event produces events equal to three, anomalies.asc_events.ErrorFrame equal to two, and anomalies.asc_events.Status equal to one.
- request-AC2 -> This backlog slice. Proof: AC2: The event filter still lists ErrorFrame and Status once each, proving that unique filter values and counted report values remain separate contracts.
- request-AC5 -> This backlog slice. Proof: AC3: The PWA report rendering shows ErrorFrame x2 and Status x1 from the backend payload without recomputing or losing counts.
- request-AC6 -> This backlog slice. Proof: AC4: Focused Node tests fail against the reviewed implementation and pass after the correction; existing Python, Node, build, and browser-smoke validations remain green.

# Decision framing
- Product framing: Not needed
- Architecture framing: Not needed

# Links
- Product brief(s): `prod_012_trustworthy_browser_local_diagnostics`
- Architecture decision(s): (none yet)
- Request: `req_026_restore_browser_local_diagnostic_data_integrity`
- Primary task(s): `task_044_deliver_browser_local_diagnostic_integrity_remediation`

# Priority
- Priority: High
- Rationale: Set by scaffold input or defaulted for grooming.
