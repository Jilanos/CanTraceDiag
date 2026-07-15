## req_000_mvp_analyse_locale_traces_can_asc - Créer le MVP d'analyse locale de traces CAN ASC
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: Construire un MVP local permettant de charger une trace CANalyzer ASC et des DBC locales, décoder les signaux, afficher des subplots temporels avec curseur valeur la plus proche, et fournir une vue trace configurable inspirée CANalyzer.
> Confidence: high
> Complexity: medium
> Theme: mvp
> Reminder: Update status/understanding/confidence and linked backlog/task references when you edit this doc.

# Needs
- Deliver a local MVP for offline analysis of CANalyzer ASC traces and local DBC files.
- Provide two primary analysis surfaces: stacked signal plots and a configurable trace view.
- Keep real traces, DBC files, CANalyzer configs, and generated caches outside Git.

# Context
- Initial usage is local under WSL.
- The MVP handles one CAN bus per acquisition.
- Primary input format is Vector CANalyzer ASCII `.asc`.
- Future formats such as BLF/MF4 must remain possible through a normalized internal model.
- Multiple DBC files may be loaded; overlaps can exist between DBC files but are not expected within one acquisition.
- Observed local traces are about 43 MB and 148 MB, with about 400k and 1.24M useful CAN frames.
- Some traces contain `CAN Status` and `ErrorFrame` events that must be visible in the trace view.

# Acceptance criteria
- AC1: The user can import a local ASC trace without committing it to the repository.
- AC2: The user can load multiple local DBC files and inspect available messages/signals.
- AC3: The MVP decodes supported frames into physical signal samples while preserving raw frames and decode failures.
- AC4: The graph view displays selected signals as stacked subplots with a shared time axis.
- AC5: Cursor values use the nearest sample; no interpolation is used.
- AC6: The trace view shows raw CAN frames, decoded message names/signals where available, and non-data events.
- AC7: The trace view has a path toward configurable columns: visibility, order, width, and display format.
- AC8: The implementation remains local-first and does not require replay controls.

# Definition of Ready (DoR)
- [x] Problem statement is explicit and user impact is clear.
- [x] Scope boundaries (in/out) are explicit.
- [x] Acceptance criteria are testable.
- [x] Dependencies and known risks are listed.

# Companion docs
- Product brief(s): `prod_002_product_brief_cantracediag_mvp`
- Architecture decision(s): `adr_002_adr_architecture_cantracediag_mvp`

# References
- `docs/product-brief.md`
- `docs/product-backlog.md`
- `docs/besoin-et-choix.md`
- `docs/adr/0001-application-web-locale.md`
- `docs/adr/0002-format-asc-et-cache-local.md`
- `docs/adr/0003-curseurs-et-graphes.md`
- `docs/adr/0004-donnees-locales-hors-depot.md`

# AI Context
- Summary: Build the first local CanTraceDiag MVP for ASC import, DBC decode, stacked plots, nearest-sample cursors, and configurable trace inspection.
- Keywords: can, canalyzer, asc, dbc, offline-analysis, plots, trace-view, local-first
- Use when: Planning or implementing the MVP.
- Skip when: Work targets future BLF/MF4 import, multi-bus support, or packaging.

# Backlog
- `item_001_mvp_analyse_locale_traces_can_asc`
