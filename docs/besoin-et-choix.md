# Analyse du besoin et choix possibles

## Objectif

Mettre en place un outil local d'analyse de traces CAN enregistrées sur véhicule via CANalyzer. L'utilisateur doit pouvoir charger une trace ASCII et les DBC associées, puis analyser les signaux décodés hors ligne.

Deux vues sont prioritaires :

1. Vue graphes : visualisation temporelle des variables/signaux sélectionnés, sans replay dynamique.
2. Vue trace : inspection chronologique des messages CAN échangés.

Le projet vise d'abord un usage local sous WSL, avec une trajectoire compatible Windows/Linux.

## Fonctionnalités attendues

### Import et décodage

- Lire les fichiers ASCII CANalyzer `.asc` en priorité.
- Préparer un modèle interne permettant d'ajouter BLF/MF4 ou d'autres exports plus tard.
- Gérer un seul bus CAN par acquisition dans le MVP.
- Charger plusieurs DBC locales, avec recouvrements possibles entre DBC mais pas attendus dans une même trace.
- Signaler les IDs dupliqués entre DBC et prévoir une résolution explicite ou par ordre de priorité.
- Décoder les signaux physiques : scale, offset, unité, valeurs min/max, endianness, signedness.
- Gérer les signaux multiplexés, au minimum en les détectant et en documentant les limites MVP.
- Conserver les trames non décodées dans la vue trace.
- Conserver les événements non-data utiles, notamment `ErrorFrame` et `CAN Status`.

### Vue graphes

- Panneau gauche listant les signaux disponibles.
- Recherche/filtre par nom de message, nom de signal, ID CAN, unité, DBC.
- Sélection multiple de signaux à afficher.
- Graphes en subplots empilés, axe temporel commun, hauteurs compactes.
- Option future pour superposer plusieurs valeurs sur un axe commun si leurs unités et échelles s'y prêtent.
- Zoom, pan, autoscale.
- Curseur simple puis double.
- Valeurs des signaux au curseur par échantillon le plus proche.
- Delta temps et delta valeur entre deux curseurs.
- Option de synchronisation du graphe avec la vue trace.

### Vue trace

- Table chronologique des trames, proche de l'expérience CANalyzer.
- Colonnes minimales : temps, canal, ID, direction, DLC, données brutes, type d'événement, nom message, signaux décodés.
- Colonnes configurables : masquage, déplacement, redimensionnement.
- Formats configurables selon les colonnes : hexadécimal, décimal, binaire.
- Filtres par ID, nom message, plage temporelle, signal, type d'événement.
- Navigation vers le temps sélectionné dans la vue graphes.
- Conservation des erreurs de décodage sous forme visible, pas silencieuse.

## Choix techniques possibles

### Option A - Application web locale Python + frontend web

Backend Python pour lire les traces et DBC, frontend web pour l'interface.

Composants possibles :

- `python-can` pour lire le format ASC CANalyzer quand il couvre le format réel.
- `cantools` pour parser et décoder les DBC.
- `pandas` / `pyarrow` pour transformer les données.
- `DuckDB` / Parquet pour indexer les traces volumineuses.
- FastAPI pour exposer les données.
- React/Vite avec Plotly, uPlot ou ECharts pour les graphes.
- Table virtualisée pour la vue trace.

Avantages :

- Très bon écosystème pour CAN et DBC côté Python.
- UI moderne, fluide, facile à enrichir.
- Bon compromis entre prototype rapide et produit maintenable.
- Peut évoluer vers un mode serveur si nécessaire, sans l'imposer au MVP local.

Inconvénients :

- Deux couches à maintenir : backend et frontend.
- Nécessite de concevoir proprement l'API de données.

Recommandation : choix retenu pour le MVP.

### Option B - Streamlit ou Dash

Application Python quasi monolithique.

Avantages :

- Très rapide pour un prototype.
- Peu de code frontend.
- Suffisant pour valider l'import, le décodage et les premiers graphes.

Inconvénients :

- Moins adapté aux très grosses traces.
- Vue trace virtualisée, curseurs avancés et synchronisation graph/table plus limitées.
- Risque de blocage UI si les fichiers deviennent lourds.

Recommandation : bon choix pour une preuve de concept rapide, moins bon comme cible finale.

### Option C - Application desktop Python, PySide6/Qt

Application installable de type outil d'ingénierie.

Avantages :

- Expérience desktop classique.
- Accès fichier local naturel.
- Bon contrôle sur l'UI, les tables et les graphes.

Inconvénients :

- Packaging plus lourd.
- Évolutions web moins naturelles.
- Plus de travail UI bas niveau.

Recommandation : pertinent si l'usage doit rester strictement local et proche d'un outil desktop.

### Option D - Tout navigateur, traitement en WebAssembly/JavaScript

Lecture et décodage côté navigateur.

Avantages :

- Pas de serveur local.
- Partage plus simple.

Inconvénients :

- Écosystème DBC/CAN moins mature qu'en Python.
- Gros fichiers plus difficiles à traiter efficacement.
- Complexité accrue pour les performances.

Recommandation : pas prioritaire pour le MVP.

## Architecture recommandée

Pour le MVP, retenir l'option A avec une séparation claire et sans replay temps réel :

```text
Trace ASC + DBC locales
      |
      v
Ingestion Python
      |
      v
Normalisation trames/events + décodage signaux
      |
      v
Stockage local Parquet/DuckDB
      |
      v
API de requête temporelle et filtres
      |
      v
UI graphes + UI trace
```

## Modèle de données minimal

### Trame ou événement brut

- `timestamp_s`
- `channel`
- `event_type`
- `arbitration_id`
- `is_extended_id`
- `dlc`
- `data`
- `direction`
- `message_name`
- `decode_status`
- `raw_line_ref`

### Signal décodé

- `timestamp_s`
- `channel`
- `arbitration_id`
- `message_name`
- `signal_name`
- `value`
- `unit`
- `raw_value`
- `quality`

## Données d'exemple observées

Les fichiers d'exemple restent hors dépôt dans `/home/paul/dev/WORK/Data_can`.

- Traces ASC observées : environ 43 Mo et 148 Mo.
- Lignes ASC observées : environ 401k et 1.36M.
- Trames CAN utiles observées : environ 400k et 1.24M.
- Durées observées : environ 267 s et 812 s.
- IDs uniques observés : 27 à 28.
- Événements observés : `CAN 1 Status` et `ErrorFrame`, avec une trace contenant un volume élevé d'ErrorFrame.
- DBC observées : 14 fichiers, petits individuellement, avec recouvrements potentiels entre systèmes.

Ces ordres de grandeur imposent une UI qui requête des plages de données au lieu de tout charger en mémoire navigateur.

## Points d'attention

- Les traces véhicule peuvent devenir volumineuses. L'UI ne doit pas charger toute la trace décodée en mémoire navigateur.
- Le décodage doit garder une séparation entre trame brute et signal calculé pour pouvoir auditer les erreurs.
- Les DBC multiples imposent une règle d'association claire : par ID et priorité de DBC dans le MVP mono-bus.
- Les signaux cycliques et événementiels ne doivent pas être traités pareil pour les curseurs.
- La valeur au curseur est la valeur la plus proche, sans interpolation.
- Les traces et DBC doivent rester locales et non versionnées.

## Décisions initiales retenues

- Format d'entrée MVP : CANalyzer ASCII `.asc`, format Vector classique.
- Format de travail : Parquet et/ou DuckDB.
- Décodage : `cantools`.
- Lecture ASC : `python-can` quand compatible, parseur dédié seulement si le format réel l'exige.
- UI cible : application web locale.
- Curseurs : valeur par échantillon le plus proche, sans interpolation.
- Vue graphes : subplots empilés avec axe temps commun.
- Vue trace : table paginée/virtualisée, filtrée côté backend, colonnes configurables.
- Repo GitHub : public possible, données locales exclues.

## Questions restantes

- Les identifiants sont-ils standard, étendus, ou mixtes dans les futurs jeux ?
- Les valeurs doivent-elles être affichées avec choix de l'unité DBC uniquement, ou avec conversions métier supplémentaires ?
- Quels signaux et colonnes sont indispensables pour valider le MVP ?
- Faut-il sauvegarder les layouts utilisateur dès la première version ?
