## item_051_shrink_docker_build_context_for_the_static_pwa_image - Shrink Docker build context for the static PWA image
> From version: 1.0.0
> Schema version: 1.0
> Status: Ready
> Understanding: 90%
> Confidence: 85%
> Progress: 0%
> Complexity: Low
> Theme: Container delivery efficiency
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.
> Indicators reviewed: 2026-08-23 09:47:01

# AI Context
- Summary: Reduce the Docker build context for the static PWA image by excluding local caches and non-production directories.
- Keywords: shrink, docker, build, context, static, pwa, image
- Use when: Editing `.dockerignore`, validating Docker image inputs, or measuring context-transfer changes.
- Skip when: Changing runtime Nginx behavior, deployment targets, or source files unrelated to Docker context size.

# Problem
- The Docker build sends a broad repository context even though the image serves a small generated static PWA.
- Local caches and non-production sources increase build time and the chance of accidental file exposure.

# Scope
- In:
  - Update `.dockerignore` to exclude `.pydeps`, Python and Node caches, tests, docs, Logics records, temporary files, CI metadata, and historical spike artifacts that are not required by the Docker build.
  - Verify that the Docker image build still has every required input to generate and serve the canonical static PWA.
  - Measure and record the before/after context size or an equivalent Docker build transfer indicator.
  - Keep the image runtime behavior and Nginx security headers unchanged.
- Out:
  - Rewriting the Dockerfile into a new build system unless the existing broad context cannot be made safe enough.
  - Changing the served artifact path or deployment target.
  - Deleting historical files from the repository.

# Acceptance criteria
- AC1: `.dockerignore` excludes `.pydeps` and other non-production directories identified in the audit while retaining all inputs required by `Dockerfile`.
- AC2: A Docker build of the static PWA image succeeds from a clean worktree after the ignore change.
- AC3: The measured context transfer is materially lower than the audited broad context, with the measurement recorded in closeout evidence.
- AC4: The existing static HTTP and MIME checks still pass against the built image.

# AC Traceability
- request-AC4 -> This backlog slice. Proof: AC1: `.dockerignore` excludes `.pydeps` and other non-production directories identified in the audit while retaining all inputs required by `Dockerfile`.
- request-AC6 -> This backlog slice. Proof: AC2: A Docker build of the static PWA image succeeds from a clean worktree after the ignore change.

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
