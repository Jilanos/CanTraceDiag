# ADR 0005 - Identité UI « instrument de mesure », thème sombre unique

## Statut

Accepté

## Contexte

L'UI du MVP est fonctionnelle mais visuellement générique : palette One Dark /
VS Code, `system-ui` proportionnel y compris pour les données numériques, aucun
lien visuel avec le domaine (analyse de bus CAN). Le public cible travaille avec
des oscilloscopes, analyseurs logiques et outils Vector ; l'identité de l'outil
doit parler ce langage. Une proposition « instrument » a été maquettée et
validée le 2026-07-16.

## Décision

- Adopter l'identité « instrument de mesure » définie dans
  [docs/design-ui.md](../design-ui.md), qui devient la référence normative de
  l'UI web.
- Séries de signaux colorées selon le code canaux d'oscilloscope
  (CH1 jaune, CH2 cyan, CH3 magenta, CH4 vert, puis extensions), à la place de
  la palette One Dark.
- Accent d'action unique ambre (`#f0a63c`) ; le bleu cesse d'être une couleur
  d'action et le cyan est réservé aux IDs d'arbitrage et au canal 2.
- Typographie à deux rôles : mono (chiffres tabulaires) pour toute donnée,
  sans pour le chrome ; micro-labels capitales espacées pour les titres de
  zones et en-têtes.
- Thème sombre unique et assumé, sans variante claire dans le MVP.
- Toutes les couleurs vivent en custom properties CSS ; le rendu canvas lit les
  tokens au lieu de constantes en dur.
- La structure de l'interface (3 zones, tracé en escalier, table paginée) est
  conservée : la refonte porte sur l'identité, pas sur l'architecture UI.

## Conséquences

- Toute évolution UI se conforme à `docs/design-ui.md` ; les dérogations passent
  par une mise à jour de la charte (et un ADR si structurant).
- `app.js` doit centraliser la lecture des couleurs (tokens via
  `getComputedStyle`) pour le plot, les swatches et les curseurs.
- L'ajout futur d'un thème clair est une décision produit qui rouvrirait cet
  ADR ; il n'est pas un simple ticket CSS.
- Les captures d'écran de documentation et les éventuels tests visuels devront
  être refaits après la refonte.
