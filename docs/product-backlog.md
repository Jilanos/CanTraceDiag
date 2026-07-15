# Product backlog initial

## P0 - MVP exploitable

### PB-001 - Importer une trace ASC CANalyzer

Lire une trace Vector ASC issue de CANalyzer 19.x, extraire les trames CAN du canal unique, et conserver les événements utiles (`ErrorFrame`, `CAN Status`) pour la vue trace.

Acceptance criteria:

- Lit les timestamps absolus en secondes.
- Lit les IDs en base décimale et les payloads CAN.
- Ignore ou classe proprement les lignes non supportées.
- Produit des statistiques d'import : durée, nombre de trames, IDs uniques, événements.

### PB-002 - Charger plusieurs DBC locales

Charger un ensemble de DBC sans les versionner, détecter les messages disponibles, et préparer une stratégie de résolution en cas d'ID dupliqué entre DBC.

Acceptance criteria:

- Liste messages et signaux par DBC.
- Signale les IDs dupliqués entre DBC.
- Permet une résolution explicite ou par priorité de configuration.

### PB-003 - Décoder les signaux

Décoder les trames en valeurs physiques en conservant les erreurs et les trames non décodées.

Acceptance criteria:

- Décode scale, offset, signedness, endianness et unité.
- Conserve la trame brute comme source d'audit.
- Marque les échecs de décodage sans bloquer l'import.

### PB-004 - Afficher les graphes temporels

Afficher plusieurs signaux en subplots empilés avec axe temps commun.

Acceptance criteria:

- Panneau gauche de recherche et sélection des signaux.
- Un subplot par signal par défaut.
- Axe temporel partagé.
- Zoom/pan synchronisés.
- Option future identifiée pour superposer des signaux compatibles sur un même axe.

### PB-005 - Ajouter les curseurs

Afficher un curseur, puis deux curseurs, avec valeurs les plus proches et deltas.

Acceptance criteria:

- Valeur du signal = échantillon le plus proche du curseur.
- Pas d'interpolation.
- Delta temps entre deux curseurs.
- Delta valeur par signal entre deux curseurs quand applicable.

### PB-006 - Fournir une vue trace configurable

Afficher une table de trace inspirée CANalyzer.

Acceptance criteria:

- Colonnes minimales : timestamp, canal, ID, direction, DLC, data, type d'événement, message, signaux décodés.
- Colonnes redimensionnables, déplaçables et masquables.
- Formats d'affichage configurables : hexadécimal, décimal, binaire lorsque pertinent.
- Filtres par temps, ID, message, signal et type d'événement.

## P1 - Ergonomie et robustesse

- Sauvegarde des layouts utilisateur.
- Recherche avancée dans les signaux.
- Export CSV/Parquet des signaux sélectionnés.
- Support des signaux multiplexés si non couvert en P0.
- Gestion de traces plus volumineuses que 150 Mo.

## P2 - Extensions

- Import BLF.
- Import MF4 si les acquisitions évoluent vers ce format.
- Packaging Windows natif.
- Gestion multi-bus.
- Profils de configuration par véhicule ou système batterie.
