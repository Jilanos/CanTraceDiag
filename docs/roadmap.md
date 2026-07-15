# Roadmap initiale

## Phase 0 - Cadrage et échantillons

- Collecter une trace ASCII représentative.
- Collecter les DBC associées.
- Identifier les volumes habituels et maximums.
- Vérifier la compatibilité du format avec `python-can`.

## Phase 1 - Ingestion

- Lire la trace ASC.
- Charger les DBC.
- Produire une table de trames brutes normalisées.
- Décoder les signaux dans une table séparée.
- Exporter un cache local Parquet.
- Ajouter des tests sur un petit jeu de données fourni.

## Phase 2 - Prototype d'analyse

- Lister les signaux disponibles.
- Requêter une plage temporelle pour un ou plusieurs signaux.
- Afficher les graphes.
- Afficher une table de trace filtrable.
- Mettre en place un curseur temporel simple.

## Phase 3 - Curseurs et synchronisation

- Ajouter deux curseurs.
- Calculer valeurs et deltas.
- Synchroniser sélection graphe -> trace.
- Synchroniser sélection trace -> graphe.

## Phase 4 - Performance et ergonomie

- Gérer les gros fichiers sans chargement complet en mémoire UI.
- Ajouter recherche avancée dans les signaux.
- Ajouter filtres persistants.
- Ajouter exports CSV/Parquet des signaux sélectionnés.

## Phase 5 - Formats et distribution

- Étudier BLF/MF4 si nécessaire.
- Packager l'application locale.
- Ajouter une documentation utilisateur.
- Ajouter des jeux de tests anonymisés.
