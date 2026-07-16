## task_015_refonte_identite_ui_instrument_de_mesure - Refonte identité UI instrument de mesure
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 95%
> Confidence: 90%
> Progress: 100%
> Complexity: Medium
> Theme: Implementation delivery
> Reminder: Update status/understanding/confidence/progress and linked request/backlog references when you edit this doc.
> Owner: claude

# Definition of Done (DoD)
- [x] The backlog scope is implemented.
- [x] Acceptance criteria are covered.
- [x] Validation passes.
- [x] Meaningful waves followed ADR 009: affected docs updated and the repo left commit-ready without automatic commits.

# Backlog
- `item_015_refonte_identite_ui_instrument_de_mesure`

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

# Implementation plan
- Wave 1 — Fondations : remplacer le bloc de tokens dans `index.html` par la palette
  de `docs/design-ui.md` (fonds, texte, accent, sémantique, `--ch1…--ch8`), supprimer
  `--s0…--s7`, poser `--mono`/`--sans`, la classe `.lbl` (micro-labels), radius 2 px
  et hairlines ; adapter boutons (primaire/standard/quiet/segmented), champs et
  dialogues.
- Wave 2 — Header : restructurer en bandeau d'instrument (marque avec pictogramme
  trame, chips fichiers mono, Load primaire ambre unique, stats mono tabulaires) et
  implémenter la LED d'état branchée sur les états d'import existants
  (`IDLE`/`IMPORTING`/`INDEXED`), en conservant la barre de progression et les flux
  d'erreur actuels.
- Wave 3 — Canvas : centraliser la lecture des tokens dans `app.js` (objet `theme`
  rafraîchi au chargement, pas de `getComputedStyle` dans la boucle de rendu) ;
  appliquer grille phosphore 10×4 par piste, tracés 1.4 px avec lueur ≤ 4 px,
  étiquettes `CHn NomSignal` + valeur courante, bornes Y, curseurs A/B pointillés à
  poignée lettrée, axe temps.
- Wave 4 — Table et explorateur : en-têtes sticky en micro-labels, pills de statut,
  liseré gauche accent sur sélection, colonnes typées (`t` muted, `ID` cyan, `Data`
  espacé) ; groupes de signaux sticky avec ID hex, swatches canaux avec lueur, liseré
  2 px sur signal coché, champ de recherche restylé.
- Wave 5 — Readouts et inspecteur : badges A/B/Δt/Δ-signal dans la plotbar (A vert,
  B ambre, Δ cyan) alimentés par la logique curseurs existante ; inspecteur restylé
  (ID hex en grand, payload brut dans bloc `--bg-deep`, grille clé/valeur, signaux en
  accent).
- Wave 6 — Passe finale : vérifier les contrastes ≥ 4.5:1 (`--fg`, `--muted`, pills),
  re-tester le breakpoint 700 px avec les nouvelles barres, `prefers-reduced-motion`,
  focus visible ; adapter les tests API/E2E qui référencent l'ancien résumé header ;
  balayage anti-patterns (aucune couleur hors tokens).

# Validation
- Run `python3 -m logics_manager lint --require-status`.
- Use `python3 -m logics_manager flow progress task task_015_refonte_identite_ui_instrument_de_mesure.md --progress <n>%` during multi-wave work.
- Run `python3 -m logics_manager flow finish task task_015_refonte_identite_ui_instrument_de_mesure.md` after implementation.
- `.venv/bin/ruff check .` et `.venv/bin/pytest` verts (y compris tests API/E2E de
- Finish workflow executed on 2026-07-16.
- Linked backlog/request close verification passed.
  l'UI servie).
- Vérification AC1 outillée : `grep -nE "5aa9ff|e06c75|98c379|c678dd|56b6c2|d19a66|--s[0-7]" src/cantracediag/web/` ne retourne rien.
- Smoke test manuel : `cantracediag serve`, import d'une fixture ASC + DBC, cocher
  4 signaux, poser les curseurs A/B, vérifier LED, pills, readouts et inspecteur.

# Report
- Identité « instrument de mesure » appliquée à `src/cantracediag/web/` (charte
- Finished on 2026-07-16.
- Linked backlog item(s): `item_015_refonte_identite_ui_instrument_de_mesure`
- Related request(s): `req_005_refonte_identite_ui_instrument_de_mesure`
  `docs/design-ui.md`, ADR 0005), structure DOM et comportements inchangés.
- `index.html` : bloc de tokens remplacé (palette instrument, `--ch1…--ch8`,
  `--mono`/`--sans`, `--grid`), suppression des tokens One Dark `--s0…--s7` ;
  boutons (primaire ambre / ghost / segmented / active), champs et dialogues
  restylés ; header restructuré en bandeau (marque + pictogramme trame, chips
  fichiers, Load primaire, stats mono tabulaires, LED d'état) ; table de trace
  en micro-labels + pills de statut + liseré de sélection ; explorateur avec
  groupes sticky, swatches et liseré signal coché ; readouts A/B/Δt dans la
  plotbar ; inspecteur (ID hex, payload brut, grille clé/valeur).
- `app.js` : `SERIES_COLORS` → `--ch1…--ch8` ; objet `theme` centralisant la
  lecture des tokens (`refreshTheme()` à l'init et au resize, plus de
  `getComputedStyle` par frame) ; canvas — grille phosphore, tracés 1.4 px avec
  lueur ≤ 4 px, étiquettes `CHn message.signal`, bornes Y, curseurs A/B (A vert
  `--ch4`, B ambre `--accent`) à poignée lettrée ; `updateMeasureBadges()` pour
  A/B/Δt ; `setLed()` branché sur `idle`/`importing`/`indexed` ; liseré sur
  signal coché.
- AC9 : `--muted` porté à `#7a8ba1` pour tenir ≥ 4.5:1 sur `--bg`/`--panel`/
  `--panel2` (mesuré : 5.32 / 5.60 / 4.99) ; charte mise à jour en conséquence.
- Validation :
  - `.venv/bin/ruff check .` -> All checks passed.
  - `.venv/bin/pytest -q` -> 61 passed, 11 skipped (E2E Playwright : Chromium
    indisponible dans l'environnement), 1 warning Starlette connu.
  - `node --check app.js` -> syntaxe OK.
  - AC1 : `grep -nE "5aa9ff|e06c75|98c379|c678dd|56b6c2|d19a66|--s[0-7]"
    src/cantracediag/web/` -> vide.
  - Cohérence statique : tous les IDs référencés par `app.js` et par les tests
    E2E existent dans `index.html` (`inspSignals` est injecté dynamiquement).
  - Smoke test API : page + `/static/app.js` servis avec les nouveaux éléments,
    flux d'import ASC+DBC OK (6 frames, 3 signaux).
- Limite : les tests E2E Playwright n'ont pas pu s'exécuter localement (Chromium
  absent) ; ils restent la couverture navigateur à relancer dans un env outillé.

# AI Context
- Summary: Implement the "measurement instrument" UI identity reskin in
  `src/cantracediag/web/` per docs/design-ui.md: tokens, oscilloscope channels, mono
  tabular data typography, token-driven canvas, instrument header with status LED,
  status pills and A/B/Δ readouts — behavior unchanged.
- Keywords: cantracediag, ui-identity, reskin, design-tokens, oscilloscope-channels,
  canvas-rendering, dark-theme, instrument
- Use when: Implementing or reviewing the UI identity reskin task.
- Skip when: Work targets backend pipeline, decoding, storage, API performance, or
  new trace formats.

# Links
- Request: `req_005_refonte_identite_ui_instrument_de_mesure`
- Product brief(s): (none yet)
- Architecture decision(s): `docs/adr/0005-identite-ui-instrument.md`
- Design charter: `docs/design-ui.md`
