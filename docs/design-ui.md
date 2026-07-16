# CanTraceDiag — Charte d'identité UI « instrument de mesure »

Ce document fige l'identité visuelle de l'interface web de CanTraceDiag. Toute
évolution de l'UI (`src/cantracediag/web/`) doit s'y conformer ; toute dérogation
passe par une mise à jour de ce document et, si la décision est structurante, par
un ADR.

Décision associée : [ADR 0005](adr/0005-identite-ui-instrument.md).
Maquette de référence validée le 2026-07-16 (proposition « instrument »).

## 1. Concept

CanTraceDiag emprunte ses codes visuels au monde de la **mesure électronique**
(oscilloscopes, analyseurs logiques, bancs de test automobile), pas à celui des
éditeurs de code. Principes directeurs :

1. **La donnée est l'écran du scope** : la zone de tracé est la surface la plus
   sombre de l'écran ; le chrome de l'application est légèrement plus clair et
   s'efface autour.
2. **Tout ce qui est une donnée est en mono** (IDs, timestamps, valeurs, payloads
   hex, compteurs) avec chiffres tabulaires ; la sans est réservée au chrome
   (labels, boutons, titres de sections).
3. **Précision d'instrument** : hairlines 1 px, radius 2 px, micro-labels en
   capitales espacées, aucun ombrage décoratif.
4. **La couleur code une information**, jamais une décoration : couleurs de
   canaux pour les séries, sémantique ok/warn/err pour les statuts, un accent
   unique pour les actions et l'état système.

## 2. Thème

**Thème sombre unique, assumé.** Comme un instrument de mesure, l'application ne
propose pas de thème clair : usage cible = lecture de courbes en sessions
longues. Ce choix est délibéré (voir ADR 0005) ; le réévaluer est une décision
produit, pas un ticket CSS.

## 3. Palette (tokens CSS)

Toutes les couleurs vivent dans `:root` sous forme de custom properties. Aucune
couleur en dur dans les règles ni dans `app.js` (le canvas lit les tokens via
`getComputedStyle`).

### Fonds et structure

| Token | Valeur | Usage |
|---|---|---|
| `--bg` | `#090d12` | fond général (bleu-noir, cast froid) |
| `--bg-deep` | `#05080c` | zone plot et champs de saisie (« écran ») |
| `--panel` | `#0e141b` | panneaux latéraux, barres |
| `--panel-2` | `#131b24` | éléments surélevés (th sticky, segmented, hover) |
| `--line` | `#1c2733` | bordures principales (hairline) |
| `--line-soft` | `#141d27` | séparateurs de lignes de table, sous-groupes |

### Texte

| Token | Valeur | Usage |
|---|---|---|
| `--fg` | `#d7e0e8` | texte principal |
| `--muted` | `#7a8ba1` | texte secondaire, labels (≥ 4.5:1 sur `--bg`/`--panel`/`--panel2`) |
| `--faint` | `#4a5a6e` | placeholders, échelles d'axes, hints |

### Accent et sémantique

| Token | Valeur | Usage |
|---|---|---|
| `--accent` | `#f0a63c` | ambre « trace » : actions primaires, LED, curseur B, valeurs inspectées |
| `--accent-dim` | `#8a5f22` | bordures hover, états intermédiaires de l'accent |
| `--ok` | `#57c99a` | décodage ok, LED indexée |
| `--warn` | `#e0a44e` | événements, decode_error |
| `--err` | `#e05c6b` | ErrorFrame, erreurs bloquantes |

Règle : l'accent est **unique** (ambre). Le bleu n'est plus une couleur d'action ;
`--ch2` (cyan) reste réservé aux IDs d'arbitrage et au canal 2.

### Canaux de tracé (code oscilloscope)

Attribution cyclique aux signaux cochés, dans l'ordre :

| Token | Valeur | Canal |
|---|---|---|
| `--ch1` | `#f5c542` | jaune |
| `--ch2` | `#3fc1e8` | cyan |
| `--ch3` | `#e86fc5` | magenta |
| `--ch4` | `#7bd88f` | vert |
| `--ch5` | `#e0a44e` | orange |
| `--ch6` | `#9a8cf5` | violet |
| `--ch7` | `#5fd4c4` | turquoise |
| `--ch8` | `#e08baa` | rose |

Les quatre premiers reprennent le code couleur Tektronix (CH1–CH4), reconnu par
le public cible. Le swatch d'un signal coché porte une lueur discrète
(`box-shadow` de sa couleur) ; le tracé canvas porte un `shadowBlur` léger
(≤ 4 px) de sa couleur de canal.

## 4. Typographie

| Rôle | Pile | Usage |
|---|---|---|
| `--mono` | `ui-monospace, "Cascadia Code", "JetBrains Mono", "SF Mono", Menlo, Consolas, monospace` | toutes les données : IDs, timestamps, valeurs, hex, noms de signaux, stats, wordmark |
| `--sans` | `"Segoe UI Variable", "Segoe UI", system-ui, -apple-system, sans-serif` | chrome : boutons, labels, titres, hints |

Règles :

- Corps de base : 12.5 px / 1.45 (sans), données en 11–11.5 px mono.
- `font-variant-numeric: tabular-nums` partout où des chiffres s'alignent
  (table de trace, readouts, axes, inspecteur).
- **Micro-labels** (`.lbl`) : sans 9.5 px, graisse 600, `letter-spacing: .14em`,
  capitales. Utilisés pour les titres de panneaux (`SIGNAUX`, `TRACE`,
  `INSPECTEUR`), les en-têtes de colonnes et les clés de readouts.
- Wordmark : mono 13 px, `CanTrace` en `--fg` + `Diag` en `--accent`, précédé du
  pictogramme « trame » (impulsion carrée dans un carré 22 px bordé accent).

## 5. Géométrie et composants

### Constantes

- Radius : **2 px** partout (boutons, chips, pills, champs). Exceptions : aucune.
- Bordures : 1 px, jamais plus épais (sauf liseré de sélection 2 px, cf. infra).
- Hauteurs de barres : header 46 px, phead 32 px, plotbar 34 px, tracebar 36 px.

### Boutons

- **Primaire** (`.primary`) : fond `--accent`, texte `#14100a`, graisse 700.
  Un seul par écran (Load).
- **Standard** : fond `--panel-2`, bordure `--line`, hover bordure `--accent-dim`.
- **Discret** (`.quiet`) : transparent, texte `--muted`, bordure au hover.
- **Segmented control** (`.seg`) : groupe de boutons joints séparés par des
  hairlines, état actif fond `--panel-2` — utilisé pour Fit/+/−/Grid.
- Focus clavier : `outline: 2px solid var(--accent); outline-offset: 2px`.

### Header « bandeau d'instrument »

De gauche à droite, sections séparées par des hairlines verticales :
marque → source (chips fichiers mono + « Changer… ») → action Load →
stats session (mono, `--muted` avec valeurs `--fg`) → **LED d'état**.

LED (`.led`) : pastille 7 px + libellé mono 10 px espacé. États : `INDEXED`
(vert, lueur), `IMPORTING` (ambre, lueur), `IDLE` (éteinte `--faint`).

### Statuts : pills

Les statuts de décodage sont des pills (`.pill`) : mono 9.5 px graisse 600,
padding 1×7, radius 2 px, bordure et fond teintés à ~15 % de la couleur
sémantique. Variantes : `ok`, `warn` (decode_error), `err` (bus error,
ErrorFrame), `mut` (unknown_id, no_database — neutre).

### Readouts de mesure (curseurs)

Badges (`.mbadge`) dans la plotbar, façon readout de scope : fond `--bg-deep`,
bordure `--line`, clé en micro-label coloré (A = `--ch4`, B = `--accent`,
Δ = `--ch2`), valeur mono tabulaire. Les deltas affichés : `Δt` et un
`Δ <signal>` par signal tracé (ou le signal focalisé).

### Zone plot (canvas)

- Fond `--bg-deep`, une piste par signal, séparées par des hairlines `--line`.
- Grille « phosphore » : 10 divisions X × 4 divisions Y par piste, trait
  `#0f1822` 1 px.
- Tracé en escalier (inchangé fonctionnellement), 1.4 px, lueur ≤ 4 px.
- Étiquette de piste en haut à gauche : `CHn NomSignal` (couleur du canal) +
  valeur courante (`--muted`) ; bornes d'échelle Y en `--faint` à gauche.
- Curseurs : trait pointillé (4/3) pleine hauteur, poignée rectangulaire en
  pied avec la lettre A/B. A = `--ch4`, B = `--accent`.
- Axe temps en pied, mono 9.5 px `--faint`.

### Table de trace

- En-têtes sticky : micro-labels sur fond `--panel-2`.
- Lignes : mono 11.5 px, séparateurs `--line-soft`, hover `#0f1720`.
- Sélection : fond translucide + **liseré gauche 2 px accent**
  (`box-shadow: inset 2px 0 0 var(--accent)`).
- Colonnes typées : `t` en `--muted`, `ID` en `--ch2`, `Data` en `--muted`
  avec `letter-spacing: .04em`, statut en pill.
- Événements (`tr.event`) : texte `--warn`.

### Explorateur de signaux

- Groupes = messages : nom en micro-label + ID hex mono `--faint`, sticky.
- Ligne signal : swatch 8 px carré (gris `--faint` si non coché, couleur de
  canal + lueur si coché), nom mono, unité mono 10 px `--muted`.
- Signal coché : liseré gauche 2 px de sa couleur de canal, fond `#0f1720`.
- Signal absent de la trace (DBC seul) : opacité .45.
- Recherche : champ fond `--bg-deep` avec icône loupe inline.

### Inspecteur

ID hex en grand (mono 15 px `--ch2`), nom de message + DBC d'origine, payload
brut dans un bloc `--bg-deep` avec les octets du signal focalisé en `--ch2`,
grille clé/valeur (clés en micro-labels), puis signaux décodés avec valeurs en
`--accent`.

## 6. Interaction et accessibilité

- Contrastes : `--fg` sur `--bg` ≈ 12:1 ; `--muted` sur `--panel` ≥ 4.5:1 ;
  vérifier tout nouveau couple token/fond à ≥ 4.5:1 pour le texte courant.
- La couleur n'est jamais le seul codage : les pills portent leur libellé, les
  signaux cochés ont checkbox + liseré, les curseurs portent leur lettre.
- Focus visible sur tout élément interactif (outline accent).
- `prefers-reduced-motion: reduce` : désactiver transitions et animations de
  lueur. Les transitions existantes restent ≤ 150 ms.
- Les raccourcis et comportements existants (molette, pan, curseurs clavier,
  ARIA du canvas) sont conservés tels quels.

## 7. Anti-patterns (à refuser en revue)

- Réintroduire une couleur One Dark / VS Code (`#5aa9ff`, `#e06c75`, `#98c379`…).
- Une couleur en dur hors tokens (CSS ou canvas).
- Un deuxième accent d'action, ou l'accent utilisé pour du décor.
- Radius > 2 px, ombres portées décoratives, dégradés hors header.
- Des données (nombres, IDs, hex) rendues en sans proportionnelle.
- Un libellé de statut codé uniquement par la couleur.
