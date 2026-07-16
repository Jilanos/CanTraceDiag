## req_005_refonte_identite_ui_instrument_de_mesure - Refonte identité UI instrument de mesure
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: Appliquer à l'UI web existante l'identité visuelle « instrument de mesure » figée dans docs/design-ui.md (tokens, canaux oscilloscope, typo mono pour les données, accent ambre unique), sans changer la structure 3 zones ni les comportements fonctionnels.
> Confidence: high
> Complexity: medium
> Theme: ui-design
> Reminder: Update status/understanding/confidence and linked backlog/task references when you edit this doc.

# Needs
- Remplacer l'identité visuelle générique actuelle (palette One Dark / VS Code,
  `system-ui` partout) par l'identité « instrument de mesure » validée sur maquette
  le 2026-07-16 et figée dans `docs/design-ui.md`.
- Donner à l'outil une identité qui parle le langage du public cible (oscilloscopes,
  analyseurs de bus) : canaux de tracé au code couleur oscilloscope, zone plot en
  « écran » plus sombre que le chrome, readouts de mesure façon scope, LED d'état.
- Rendre toutes les données numériques (timestamps, IDs, valeurs, payloads hex)
  lisibles et alignées : mono + chiffres tabulaires partout où il y a de la donnée.
- Centraliser toutes les couleurs en tokens CSS et faire lire ces tokens par le rendu
  canvas, afin que la charte soit appliquée à un seul endroit et vérifiable en revue.
- Conserver strictement les comportements existants : import, sélection de signaux,
  zoom/pan, curseurs A/B et deltas, pagination de trace, filtres, colonnes
  configurables, résolution de conflits DBC, accessibilité clavier/ARIA.

# Context
- L'UI vit dans `src/cantracediag/web/index.html` (CSS inline, ~270 lignes) et
  `src/cantracediag/web/app.js` (~1170 lignes, rendu plot en canvas 2D avec couleurs
  en dur `--s0…--s7` côté CSS et lecture directe côté JS).
- Le CSS actuel est déjà tokenisé (`--bg`, `--panel`, `--accent`, `--s0…--s7`), ce qui
  rend la migration essentiellement déclarative pour les panneaux ; le travail réel
  porte sur le canvas (grille, tracés, curseurs, étiquettes), le header restructuré,
  les pills de statut et les readouts de mesure.
- La charte normative est `docs/design-ui.md` ; la décision et sa justification sont
  dans `docs/adr/0005-identite-ui-instrument.md`. Le thème reste sombre unique
  (choix assumé, pas d'oubli).
- La structure 3 zones (explorateur / plot+trace / inspecteur), le tracé en escalier
  sans interpolation (ADR 0003) et la pagination restent inchangés : la refonte est
  une peau, pas une réarchitecture.
- Une maquette HTML statique de référence a été validée (proposition « instrument »
  du 2026-07-16) ; elle sert de cible visuelle, `docs/design-ui.md` fait foi en cas
  d'écart.

# Product decisions
- `docs/design-ui.md` devient la référence normative : tokens, typographie, géométrie
  (radius 2 px, hairlines), composants (pills, mbadges, LED, segmented control) et
  anti-patterns y sont figés ; toute dérogation passe par une mise à jour de la charte.
- Couleurs de séries : attribution cyclique `--ch1…--ch8` (code oscilloscope) dans
  l'ordre de sélection des signaux ; suppression des tokens One Dark `--s0…--s7`.
- Accent d'action unique ambre `--accent` ; un seul bouton primaire par écran (Load).
- Le header devient un bandeau d'instrument : marque avec pictogramme trame, chips
  fichiers, stats mono, LED d'état (`INDEXED` / `IMPORTING` / `IDLE`) remplaçant le
  résumé texte libre.
- Les statuts de décodage deviennent des pills libellées (jamais la couleur seule) ;
  les curseurs A/B gagnent des readouts `A`, `B`, `Δt`, `Δ signal` dans la plotbar.
- Aucune dépendance frontend nouvelle : CSS/JS vanilla, polices système (piles mono
  et sans définies dans la charte), CSP inchangée.
- Le responsive existant (breakpoint 700 px) est conservé et adapté à la nouvelle
  peau, sans nouvelle exigence responsive dans cette requête.

# Acceptance criteria
- AC1: Plus aucune couleur One Dark (`#5aa9ff`, `#e06c75`, `#98c379`, `#c678dd`,
  `#56b6c2`, `#d19a66`, `#e0a44e` en tant que série) ni token `--s0…--s7` dans
  `index.html` et `app.js` ; les tokens et valeurs correspondent à ceux de
  `docs/design-ui.md`.
- AC2: Le rendu canvas (grille, tracés, curseurs, étiquettes de piste, axe temps) lit
  ses couleurs depuis les custom properties CSS ; aucune couleur en dur dans `app.js`.
- AC3: Les séries affichées utilisent les canaux `--ch1…--ch8` avec étiquette de piste
  `CHn NomSignal` et swatch assorti dans l'explorateur (avec liseré 2 px sur signal
  coché).
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
  les tests E2E/API qui touchent l'UI servie.

# Suggested implementation slices
- Slice 1: Remplacer le bloc de tokens CSS et la typographie de base dans
  `index.html` (palette, `--mono`/`--sans`, `.lbl`, radius, hairlines) ; adapter
  panneaux, boutons, champs, dialogues.
- Slice 2: Restructurer le header en bandeau d'instrument (marque, chips, LED d'état
  branchée sur les états d'import existants).
- Slice 3: Migrer le rendu canvas de `app.js` vers les tokens (lecture
  `getComputedStyle` centralisée), grille phosphore, étiquettes `CHn`, curseurs A/B
  stylés, lueur des tracés.
- Slice 4: Table de trace (en-têtes micro-labels, pills de statut, liseré de
  sélection, colonnes typées) et explorateur (groupes sticky avec ID hex, swatches,
  liseré signal coché).
- Slice 5: Readouts de mesure A/B/Δ dans la plotbar et inspecteur (ID hex en grand,
  payload brut mis en évidence, grille clé/valeur) ; passe finale contrastes,
  responsive 700 px et `prefers-reduced-motion`.

# Out of scope
- Thème clair ou bascule de thème (décision ADR 0005 ; rouvrirait l'ADR).
- Toute évolution fonctionnelle : nouveaux filtres, export, statistiques entre
  curseurs, replay.
- Refonte responsive/accessibilité au-delà de l'existant (couvert par
  `item_012_p2_ameliorer_ui_accessibilite_responsive`).
- Introduction d'un framework frontend, d'un bundler ou de webfonts.
- Packaging, captures marketing, documentation utilisateur illustrée.

# Definition of Ready (DoR)
- [x] Problem statement is explicit and user impact is clear.
- [x] Scope boundaries (in/out) are explicit.
- [x] Acceptance criteria are testable.
- [x] Dependencies and known risks are listed.

# Dependencies and risks
- `app.js` mélange logique et constantes de rendu ; centraliser la lecture des tokens
  demande un point d'entrée unique (ex. objet `theme` rafraîchi au chargement) pour
  éviter des lectures `getComputedStyle` dispersées et coûteuses dans la boucle de
  rendu.
- Les tests E2E/API qui inspectent le HTML servi peuvent référencer des classes ou
  libellés modifiés (résumé header remplacé par stats + LED) : adapter les attentes
  sans affaiblir les assertions fonctionnelles.
- La lueur (`shadowBlur`) sur canvas a un coût de rendu ; à garder ≤ 4 px et à
  désactiver si une régression de fluidité est mesurée sur les grosses traces.
- Risque de dérive pendant la migration : toute couleur ajoutée hors tokens doit être
  refusée en revue (section anti-patterns de la charte).
- Le breakpoint mobile existant doit être re-testé : les nouvelles barres (readouts,
  segmented) ajoutent de la largeur en plotbar.

# Companion docs
- Product brief(s): (none yet)
- Architecture decision(s): `docs/adr/0005-identite-ui-instrument.md`
- Design charter: `docs/design-ui.md`

# References
- `docs/design-ui.md`
- `docs/adr/0005-identite-ui-instrument.md`
- `docs/adr/0003-curseurs-et-graphes.md`
- `src/cantracediag/web/index.html`
- `src/cantracediag/web/app.js`
- `tests/test_api.py`
- `logics/backlog/item_012_p2_ameliorer_ui_accessibilite_responsive.md`

# AI Context
- Summary: Reskin the CanTraceDiag web UI to the frozen "measurement instrument"
  identity (oscilloscope channel colors, amber accent, mono tabular data typography,
  token-driven canvas rendering) without changing layout structure or behavior.
- Keywords: cantracediag, ui-identity, design-tokens, oscilloscope-channels,
  dark-theme, canvas-rendering, reskin, design-charter
- Use when: Implementing or reviewing UI changes in `src/cantracediag/web/`, applying
  the design charter, or checking visual regressions against docs/design-ui.md.
- Skip when: Work targets backend pipeline, decoding, storage, API performance, or
  new trace formats.

# Backlog
- none
- `item_015_refonte_identite_ui_instrument_de_mesure`
