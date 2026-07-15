# ADR 0002 - ASC en entrée MVP et cache local indexé

## Statut

Accepté

## Contexte

Les traces disponibles sont principalement au format CANalyzer ASCII `.asc`. Des formats futurs comme BLF ou MF4 peuvent être nécessaires plus tard. Les exemples observés font environ 43 Mo et 148 Mo, avec 400k à 1.24M trames utiles et des événements non-data à conserver.

## Décision

Le MVP cible le format ASC et normalise les données dans un modèle interne indépendant du format source. Les données importées doivent pouvoir être cachées localement dans un format indexable, typiquement Parquet et/ou DuckDB.

## Conséquences

- Le parser ASC peut être implémenté et testé en premier.
- L'ajout de BLF/MF4 devra produire le même modèle interne.
- Le frontend interroge des plages temporelles et filtres au lieu de charger toute la trace.
- Les fichiers `.asc`, `.dbc`, `.blf`, `.mf4`, `.parquet`, `.duckdb` restent exclus du dépôt.
