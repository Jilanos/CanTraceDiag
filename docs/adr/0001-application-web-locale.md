# ADR 0001 - Application web locale pour le MVP

## Statut

Accepté

## Contexte

Le projet doit analyser localement des traces CANalyzer ASC et des DBC, avec une interface riche : sélection de signaux, graphes synchronisés, curseurs, deltas et vue trace configurable. L'usage initial se fait sous WSL, avec une compatibilité Windows/Linux souhaitée à terme.

## Décision

Construire le MVP comme une application web locale :

- Backend Python pour ingestion ASC, chargement DBC, décodage et indexation.
- Frontend web pour graphes, panneau de signaux et table de trace.
- Stockage/cache local pour éviter de charger toute la trace dans le navigateur.

## Alternatives considérées

- Streamlit/Dash : plus rapide pour prototyper, mais moins adapté à une table trace configurable et performante.
- Desktop Qt/PySide : expérience locale solide, mais packaging et développement UI plus lourds.
- Tout navigateur : moins bon écosystème CAN/DBC que Python.

## Conséquences

- Deux surfaces à maintenir : backend et frontend.
- Meilleure trajectoire pour les performances, la configurabilité de la trace et l'extension de formats.
- Compatible avec un usage local strict sans envoyer les traces ni DBC dans le dépôt.
