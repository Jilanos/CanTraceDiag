# Product brief - CanTraceDiag MVP

## Problème

Les traces CAN enregistrées sur véhicule via CANalyzer doivent aujourd'hui être relues dans un environnement d'analyse lourd. Le besoin est d'avoir un outil local, orienté diagnostic, pour charger une trace ASC et les DBC associées, visualiser les signaux dans le temps, poser des curseurs, et inspecter les trames comme dans une vue trace CANalyzer.

## Utilisateurs cibles

- Ingénieurs système batterie et véhicule.
- Développeurs qui analysent des acquisitions CAN.
- Diagnosticiens qui veulent comparer rapidement l'évolution de signaux et les trames brutes.

## Périmètre MVP

- Usage local sous WSL.
- Entrée principale : fichier CANalyzer ASCII `.asc`.
- Un seul bus CAN par acquisition.
- DBC multiples chargées localement.
- Pas de recouvrement d'ID attendu dans une même trace.
- Recouvrements possibles entre DBC, gérés par sélection explicite ou ordre de priorité.
- Graphes temporels en subplots empilés avec axe temps commun.
- Curseur basé sur l'échantillon le plus proche, sans interpolation.
- Vue trace inspirée CANalyzer avec colonnes configurables.
- Données d'acquisition, DBC et configs CANalyzer non versionnées dans Git.

## Hors périmètre MVP

- Replay temps réel avec lecture/pause/vitesse.
- Support multi-bus.
- Collaboration multi-utilisateur.
- Import BLF/MF4 en première livraison.
- Packaging Windows natif.
- Cloud ou stockage distant de traces.

## Signaux de succès

- Une trace ASC de 40 à 150 Mo peut être importée localement.
- Les DBC locales permettent de lister les messages et signaux disponibles.
- L'utilisateur peut sélectionner plusieurs signaux et voir leurs évolutions en subplots synchronisés.
- Le curseur affiche la valeur la plus proche et le timestamp associé.
- La vue trace affiche les trames brutes, les messages décodés, les `ErrorFrame`/`Status`, et permet au minimum filtrage et configuration de colonnes.

## Données d'exemple observées localement

Les fichiers de référence restent hors dépôt, dans `/home/paul/dev/WORK/Data_can`.

- Deux traces ASC observées : environ 43 Mo et 148 Mo.
- Durées observées : environ 267 s et 812 s.
- Trames CAN utiles observées : environ 400k et 1.24M.
- IDs uniques observés : 27 à 28.
- Events non-data observés : lignes `CAN 1 Status` et `ErrorFrame`, avec un cas contenant environ 116k `ErrorFrame`.
- DBC observées : 14 fichiers, avec plusieurs systèmes et recouvrements potentiels entre DBC.

## Questions ouvertes

- Quel jeu minimal de signaux doit servir de référence d'acceptation ?
- Faut-il exposer les signaux multiplexés dès le MVP ou les marquer comme limitation temporaire ?
- Quels formats de colonnes trace sont prioritaires : hex, décimal, binaire, raw bytes, valeurs physiques ?
- Faut-il sauvegarder les layouts utilisateur des graphes et colonnes dès la première version ?
