# Roadmap initiale

## Phase 0 - Cadrage et échantillons

- Confirmer les décisions produit et architecture.
- Identifier les volumes habituels et maximums à partir des traces locales.
- Vérifier la compatibilité du format avec `python-can`.
- Définir les fixtures synthétiques qui pourront être versionnées.

## Phase 1 - Ingestion

- Lire la trace ASC.
- Charger les DBC.
- Produire une table de trames brutes normalisées.
- Décoder les signaux dans une table séparée.
- Exporter un cache local Parquet.
- Ajouter des tests sur un petit jeu de données fourni.
- Conserver `ErrorFrame` et `CAN Status` comme événements de trace.

## Phase 2 - Prototype d'analyse

- Lister les signaux disponibles.
- Requêter une plage temporelle pour un ou plusieurs signaux.
- Afficher les graphes en subplots empilés avec axe temps commun.
- Afficher une table de trace filtrable et virtualisée.
- Mettre en place un curseur temporel simple avec valeur la plus proche.

## Phase 3 - Curseurs et synchronisation

- Ajouter deux curseurs.
- Calculer valeurs et deltas.
- Synchroniser sélection graphe -> trace.
- Synchroniser sélection trace -> graphe.
- Ajouter les options de colonnes trace : masquage, déplacement, largeur, format.

## Phase 4 - Performance et ergonomie

- Gérer les gros fichiers sans chargement complet en mémoire UI.
- Ajouter recherche avancée dans les signaux.
- Ajouter filtres persistants.
- Ajouter exports CSV/Parquet des signaux sélectionnés.
- Sauvegarder les layouts utilisateur.

## Phase 5 - Formats et distribution

- Étudier BLF/MF4 si nécessaire.
- Packager l'application locale.
- Ajouter une documentation utilisateur.
- Ajouter des jeux de tests anonymisés.
