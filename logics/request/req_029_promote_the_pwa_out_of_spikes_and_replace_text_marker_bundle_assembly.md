## req_029_promote_the_pwa_out_of_spikes_and_replace_text_marker_bundle_assembly - Promote the PWA out of spikes and replace text-marker bundle assembly
> From version: 1.0.0
> Schema version: 1.0
> Status: Draft
> Understanding: 80%
> Confidence: 70%
> Complexity: High
> Theme: Static PWA delivery integrity
> Reminder: Update status/understanding/confidence and linked backlog/task references when you edit this doc.

# AI Context
- Summary: Move the production PWA out of `spikes/`, replace `replaceBlock` text rewriting with an injected transport, and archive the historical 500 MB benchmark spike.
- Keywords: pwa, spikes, promotion, transport, backend port, replaceBlock, archive
- Use when: Restructuring where the delivered PWA lives or how its bundle is assembled from the shared UI shell.
- Skip when: Fixing delivered behavior inside the current build, CI coverage, or Docker context.

# Needs
- Make the deployed artifact live in a first-class source location instead of an exploration directory, so its build inputs and ownership are unambiguous.
- Replace source rewriting by text markers with an explicit transport boundary, so an edited comment in `src/cantracediag/web/js/` can no longer break the production build.
- Remove the historical `spikes/pwa-500mb/` benchmark material from the working tree once its measurements are preserved as documentation.

# Context
- Audit finding C3 in `docs/audit-2026-08-23.md`, carried forward from `req_028` as residual structural work explicitly left out of that slice.
- The deployed image is built from `spikes/pwa-local-engine/` with cross dependencies on `src/cantracediag/web/` (HTML shell, CSS, JS, SVG).
- `buildProductAppSource()` in `spikes/pwa-local-engine/build-browser.mjs` still calls `replaceBlock()` three times against literal source strings, one of which is a code comment. `req_028` removed the duplicated module list but not the rewriting itself.
- The shared UI shell has no explicit interface between the FastAPI transport and the local PWA backend; that coupling is what made the fullscreen omission possible.
- `spikes/pwa-500mb/` is a July benchmark that is now excluded from the Docker context but still tracked in git.

# Acceptance criteria
- AC1: The production PWA build inputs live outside `spikes/`, with the deployed artifact and its Dockerfile inputs unchanged in content.
- AC2: The product UI selects its backend through an explicit injected transport (FastAPI client or local PWA backend) rather than through build-time source rewriting; `replaceBlock` is removed.
- AC3: A comment or formatting change inside `src/cantracediag/web/js/` cannot break the static build, and a test demonstrates this.
- AC4: `spikes/pwa-500mb/` is archived or removed, with its measurements retained in `docs/`.
- AC5: Existing Python tests, Node PWA tests, the static build, the generated-site browser smoke, and the container MIME check all remain green.

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
- spikes/pwa-local-engine/build-browser.mjs
- spikes/pwa-local-engine/product-modules.mjs
- src/cantracediag/web/index.html
- Dockerfile

# Backlog
- none
