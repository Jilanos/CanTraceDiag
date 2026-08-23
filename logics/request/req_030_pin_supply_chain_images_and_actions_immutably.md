## req_030_pin_supply_chain_images_and_actions_immutably - Pin supply-chain images and actions immutably
> From version: 1.0.0
> Schema version: 1.0
> Status: Draft
> Understanding: 85%
> Confidence: 75%
> Complexity: Medium
> Theme: Release and supply chain
> Reminder: Update status/understanding/confidence and linked backlog/task references when you edit this doc.

# AI Context
- Summary: Pin Docker base images by digest and GitHub Actions by commit SHA, with an automated update path, so the publishing path cannot drift under mutable tags.
- Keywords: supply chain, pinning, digest, sha, dependabot, release, docker, actions
- Use when: Changing base images, action references, or the dependency update policy for the release path.
- Skip when: Changing what the workflows validate rather than what they resolve to.

# Needs
- Make the image that reaches production reproducible from the tag alone, rather than depending on when the build ran.
- Apply one pinning policy across `ci.yml` and `release.yml` instead of two.
- Keep pinned references maintainable, so pinning does not decay into stale, unpatched dependencies.

# Context
- Audit finding C5 in `docs/audit-2026-08-23.md`, carried forward from `req_028` as residual supply-chain work.
- `req_028` took the smallest safe step: `release.yml` now pins the checkout and setup actions to the same exact versions `ci.yml` uses, instead of floating majors. Nothing is pinned by SHA yet.
- `Dockerfile` still uses mutable tags for its Node build image and its unprivileged Nginx runtime image.
- `release.yml` still uses floating majors for its third-party actions: the docker login, buildx setup, metadata and build-push actions, the SSH deploy action, and the GitHub release action.
- Pinning the publishing path by hand carries a real risk of typing a reference that does not resolve, which fails only at release time; each pin must be verified before it is merged.

# Acceptance criteria
- AC1: Both `Dockerfile` base images are pinned by digest, with the tag retained in a comment for readability.
- AC2: Every third-party GitHub Action in `ci.yml` and `release.yml` is pinned by commit SHA with the human-readable version in a trailing comment.
- AC3: Each pin is verified to resolve before merge, and the verification method is recorded in the task closeout.
- AC4: An automated update path (Dependabot or equivalent) keeps the pinned references current, covering both `github-actions` and `docker` ecosystems.
- AC5: A full release runs end to end on the pinned workflows without manual intervention.

# Definition of Ready (DoR)
- [x] Problem statement is explicit and user impact is clear.
- [x] Scope boundaries (in/out) are explicit.
- [x] Acceptance criteria are testable.
- [x] Dependencies and known risks are listed.

# Companion docs
- Product brief(s): `prod_013_reliable_static_pwa_delivery`
- Architecture decision(s): (none yet)

# References
- docs/audit-2026-08-23.md
- logics/request/req_028_harden_static_pwa_delivery_and_release_validation.md
- .github/workflows/ci.yml
- .github/workflows/release.yml
- Dockerfile

# Backlog
- none
