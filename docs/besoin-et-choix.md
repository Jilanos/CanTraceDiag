# Analyse du besoin et choix possibles

## Objectif

Mettre en place un outil de relecture de traces CAN enregistrées sur véhicule via CANalyzer. L'utilisateur doit pouvoir charger une trace ASCII et les DBC associées, puis analyser les signaux décodés comme si l'acquisition était rejouée hors ligne.

Deux vues sont prioritaires :

1. Vue graphes : visualisation temporelle des variables/signaux sélectionnés.
2. Vue trace : inspection chronologique des messages CAN échangés.

## Fonctionnalités attendues

### Import et décodage

- Lire les fichiers ASCII CANalyzer.
- Charger une ou plusieurs DBC.
- Associer les messages aux bons bus/canaux si plusieurs réseaux sont présents.
- Décoder les signaux physiques : scale, offset, unité, valeurs min/max, endianness, signedness.
- Gérer les signaux multiplexés.
- Conserver les trames non décodées dans la vue trace.

### Vue graphes

- Panneau gauche listant les signaux disponibles.
- Recherche/filtre par nom de message, nom de signal, ID CAN, unité, bus.
- Sélection multiple de signaux à afficher.
- Courbes temporelles avec zoom, pan, autoscale.
- Curseur simple ou double.
- Valeurs des signaux au curseur.
- Delta temps et delta valeur entre deux curseurs.
- Option de synchronisation du graphe avec la vue trace.

### Vue trace

- Table chronologique des trames.
- Colonnes minimales : temps, canal, ID, DLC, données brutes, nom message, signaux décodés.
- Filtres par ID, nom message, bus, plage temporelle, signal.
- Navigation vers le temps sélectionné dans la vue graphes.
- Conservation des erreurs de décodage sous forme visible, pas silencieuse.

## Choix techniques possibles

### Option A - Application web locale Python + frontend web

Backend Python pour lire les traces et DBC, frontend web pour l'interface.

Composants possibles :

- `python-can` pour lire le format ASC CANalyzer.
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
- Peut évoluer vers un mode serveur ou partage de sessions.

Inconvénients :

- Deux couches à maintenir : backend et frontend.
- Nécessite de concevoir proprement l'API de données.

Recommandation : meilleur choix pour ce projet si l'objectif est un outil ergonomique et durable.

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
- Évolutions collaboratives ou web moins naturelles.
- Plus de travail UI bas niveau.

Recommandation : pertinent si l'usage doit rester strictement local et proche d'un outil de calibration/diagnostic desktop.

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

Pour le MVP, retenir l'option A avec une séparation claire :

```text
Trace ASC + DBC
      |
      v
Ingestion Python
      |
      v
Normalisation trames + décodage signaux
      |
      v
Stockage local Parquet/DuckDB
      |
      v
API de requête temporelle
      |
      v
UI graphes + UI trace
```

## Modèle de données minimal

### Trame brute

- `timestamp_s`
- `channel`
- `arbitration_id`
- `is_extended_id`
- `dlc`
- `data`
- `direction`
- `message_name`
- `decode_status`

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

## Points d'attention

- Les traces véhicule peuvent devenir très volumineuses. L'UI ne doit pas charger toute la trace décodée en mémoire navigateur.
- Le décodage doit garder une séparation entre trame brute et signal calculé pour pouvoir auditer les erreurs.
- Les DBC multiples imposent une règle d'association claire : par bus, par ID, ou par priorité de DBC.
- Les signaux cycliques et événementiels ne doivent pas être traités pareil pour les curseurs.
- Il faudra décider si la valeur au curseur est interpolée, retenue par échantillon précédent, ou marquée absente.

## Décisions initiales proposées

- Format d'entrée MVP : CANalyzer ASCII `.asc`.
- Format de travail : Parquet partitionné par trace et éventuellement par bus.
- Décodage : `cantools`.
- Lecture ASC : `python-can` quand compatible, parseur dédié seulement si le format réel l'exige.
- UI cible : application web locale.
- Curseurs : valeur par dernier échantillon connu avant le curseur, avec option future d'interpolation pour les signaux analogiques.
- Vue trace : table paginée/virtualisée, filtrée côté backend.

## Questions à confirmer avec les premiers fichiers

- Les traces contiennent-elles plusieurs bus CAN ?
- Les identifiants sont-ils standard, étendus, ou mixtes ?
- Les traces ASCII CANalyzer utilisent-elles un format classique Vector ASC ou un export personnalisé ?
- Les DBC ont-elles des messages dupliqués entre bus ?
- Les valeurs doivent-elles être affichées avec choix de l'unité DBC uniquement, ou avec conversions métier supplémentaires ?
- Faut-il rejouer la trace en temps réel avec une barre de lecture, ou seulement naviguer dans le temps ?
