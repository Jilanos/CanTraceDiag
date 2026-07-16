## item_015_refonte_identite_ui_instrument_de_mesure - Refonte identité UI instrument de mesure
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 95%
> Confidence: 90%
> Progress: 100%
> Complexity: Medium
> Theme: Operator workflow and runtime integration
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
L'UI web actuelle est fonctionnelle mais visuellement générique : palette One Dark /
VS Code, `system-ui` proportionnel y compris pour les données numériques, aucun lien
visuel avec le domaine de l'analyse de bus CAN.

Ce backlog applique l'identité « instrument de mesure » figée dans `docs/design-ui.md`
(charte normative) et actée par l'ADR 0005 : canaux de tracé au code couleur
oscilloscope, accent ambre unique, typo mono tabulaire pour toute donnée, rendu canvas
piloté par les tokens CSS. La structure 3 zones et tous les comportements existants
sont conservés à l'identique : c'est une peau, pas une réarchitecture.

# Scope
- In:
  - remplacement des tokens CSS et de la typographie de base dans `index.html`
    (palette charte, `--mono`/`--sans`, micro-labels, radius 2 px, hairlines) ;
  - header restructuré en bandeau d'instrument (marque, chips fichiers, Load primaire
    ambre, stats mono, LED d'état branchée sur les états d'import réels) ;
  - migration du rendu canvas de `app.js` vers les tokens (lecture `getComputedStyle`
    centralisée), grille phosphore, étiquettes `CHn`, curseurs A/B stylés, lueur ≤ 4 px ;
  - table de trace (micro-labels, pills de statut, liseré de sélection, colonnes
    typées) et explorateur (groupes sticky avec ID hex, swatches canaux, liseré coché) ;
  - readouts de mesure A/B/Δt/Δ-signal dans la plotbar et inspecteur restylé ;
  - passe finale contrastes ≥ 4.5:1, responsive 700 px, `prefers-reduced-motion`.
- Out:
  - thème clair ou bascule de thème (ADR 0005) ;
  - toute évolution fonctionnelle (filtres, export, statistiques, replay) ;
  - refonte responsive/accessibilité au-delà de l'existant (suivie par `item_012`) ;
  - framework frontend, bundler, webfonts, changement de CSP.

# Acceptance criteria
- AC1: Plus aucune couleur One Dark (`#5aa9ff`, `#e06c75`, `#98c379`, `#c678dd`,
  `#56b6c2`, `#d19a66`, `#e0a44e` en tant que série) ni token `--s0…--s7` dans
  `index.html` et `app.js` ; les tokens et valeurs correspondent à `docs/design-ui.md`.
- AC2: Le rendu canvas (grille, tracés, curseurs, étiquettes de piste, axe temps) lit
  ses couleurs depuis les custom properties CSS ; aucune couleur en dur dans `app.js`.
- AC3: Les séries affichées utilisent les canaux `--ch1…--ch8` avec étiquette de piste
  `CHn NomSignal` et swatch assorti dans l'explorateur, avec liseré 2 px sur signal
  coché.
- AC4: Toutes les données numériques (table de trace, readouts, inspecteur, stats du
  header, axes) sont rendues en mono avec `font-variant-numeric: tabular-nums`.
- AC5: Le header présente marque, chips fichiers, bouton Load primaire ambre, stats et
  LED d'état ; la LED reflète réellement l'état (`IDLE` sans analyse, `IMPORTING`
  pendant un import, `INDEXED` après succès) et la barre de progression reste
  fonctionnelle.
- AC6: Les statuts de trace sont des pills libellées (`ok`, `decode_error`,
  `unknown_id`/`no_database` neutres, erreurs bus) et la ligne sélectionnée porte le
  liseré gauche accent.
- AC7: Les curseurs A/B affichent des readouts `A`, `B`, `Δt` (et delta de valeur par
  signal) dans la plotbar, avec les couleurs de la charte (A vert, B ambre).
- AC8: Tous les comportements existants restent fonctionnels à l'identique : import
  fichiers/dossier DBC, conflits DBC, recherche et favoris signaux, zoom/pan/fit,
  grid, filtres et colonnes de trace, pagination, inspecteur, raccourcis clavier,
  focus visible, ARIA du canvas, `prefers-reduced-motion`.
- AC9: Les contrastes texte respectent ≥ 4.5:1 sur leurs fonds (vérification faite au
  moins pour `--fg`, `--muted` et les pills sur leurs fonds respectifs).
- AC10: La suite de tests existante reste verte (`ruff check .` + `pytest`), y compris
  les tests E2E/API qui touchent l'UI servie, après adaptation des attentes liées au
  header restructuré.

# AC Traceability
- request-AC1 -> This backlog slice. Proof: AC1 (tokens charte, zéro One Dark résiduel).
- request-AC2 -> This backlog slice. Proof: AC2 (canvas piloté par tokens).
- request-AC3 -> This backlog slice. Proof: AC3 (canaux CH1…CH8 et swatches).
- request-AC4 -> This backlog slice. Proof: AC4 (mono tabulaire pour les données).
- request-AC5 -> This backlog slice. Proof: AC5 (bandeau d'instrument et LED d'état).
- request-AC6 -> This backlog slice. Proof: AC6 (pills de statut et liseré sélection).
- request-AC7 -> This backlog slice. Proof: AC7 (readouts A/B/Δ).
- request-AC8 -> This backlog slice. Proof: AC8 (iso-fonctionnalité complète).
- request-AC9 -> This backlog slice. Proof: AC9 (contrastes ≥ 4.5:1).
- request-AC10 -> This backlog slice. Proof: AC10 (ruff + pytest verts).

# Decision framing
- Product framing: Not needed
- Product signals: (none detected)
- Product follow-up: No product brief follow-up is expected based on current signals.
- Architecture framing: Settled
- Architecture signals: identité visuelle et thème figés hors code
- Architecture follow-up: décision actée dans `docs/adr/0005-identite-ui-instrument.md` ;
  la charte `docs/design-ui.md` fait foi, pas de nouvel ADR attendu.

# Links
- Product brief(s): (none yet)
- Architecture decision(s): `docs/adr/0005-identite-ui-instrument.md`
- Request: `logics/request/req_005_refonte_identite_ui_instrument_de_mesure.md`
- Primary task(s): (none yet)

# AI Context
- Summary: Appliquer l'identité « instrument de mesure » (charte docs/design-ui.md) à
  l'UI web : tokens, canaux oscilloscope, typo mono tabulaire, canvas piloté par
  tokens, header instrument, pills et readouts — sans changement fonctionnel.
- Keywords: backlog-groom, ui-identity, design-tokens, oscilloscope-channels, reskin,
  canvas-rendering, dark-theme, design-charter
- Use when: Use when implementing or reviewing the delivery slice for the instrument
  UI identity reskin in `src/cantracediag/web/`.
- Skip when: Skip when the change is unrelated to this delivery slice or its linked
  request (backend, decoding, storage, API performance, new formats).

# Implementation notes
- Centraliser la lecture des tokens dans `app.js` (objet `theme` rafraîchi au
  chargement) plutôt que des `getComputedStyle` dispersés dans la boucle de rendu.
- Suivre les slices de la request : tokens/typo → header/LED → canvas → table et
  explorateur → readouts/inspecteur et passe finale.
- Refuser en revue toute couleur hors tokens (section anti-patterns de la charte).
- Surveiller le coût du `shadowBlur` canvas sur les grosses traces ; le désactiver si
  une régression de fluidité est mesurée.
- Re-tester le breakpoint 700 px : les readouts et le segmented control élargissent la
  plotbar.

# Priority
- Priority: Medium
- Rationale: Forte valeur d'identité produit et de lisibilité des données, mais aucune
  correction fonctionnelle ni gain de performance ; passe après les travaux P0/P1 de
  robustesse déjà engagés.

# Notes
- Hybrid rationale: Derived from request `req_005_refonte_identite_ui_instrument_de_mesure` and kept bounded to one coherent delivery slice.
- Source file: `logics/request/req_005_refonte_identite_ui_instrument_de_mesure.md`.
- Generated locally by logics-manager.
- Task `task_015_refonte_identite_ui_instrument_de_mesure` was finished via `logics-manager flow finish task` on 2026-07-16.

# Tasks
- `task_015_refonte_identite_ui_instrument_de_mesure`
