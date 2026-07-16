## item_014_optimiser_le_chargement_des_grosses_traces_par_decodage_a_la_demande - Optimiser le chargement des grosses traces par décodage à la demande
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: High
> Theme: Operator workflow and runtime integration
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
Le chargement actuel des traces ASC volumineuses avec DBC décode toutes les trames et
matérialise tous les signaux dans `samples` pendant l'import. Ce travail bloque la mise
à disposition de la trace alors que l'opérateur affiche généralement seulement 2 à 8
signaux.

Ce backlog doit transformer ce comportement en modèle paresseux : importer rapidement
les trames brutes et les métadonnées nécessaires, puis décoder uniquement les signaux
consultés par l'UI ou par les fonctions de diagnostic.

# Scope
- In:
  - index brut des trames, événements, timestamps, IDs, payloads, direction et
    métadonnées DBC utiles à la navigation ;
  - décodage ciblé par signal et plage temporelle pour `/api/series` ;
  - cache local de session pour les séries déjà décodées ;
  - adaptation de `/api/signals`, `/api/cursor`, `/api/frame-signals` et du filtre
    trace par signal ;
  - tests de non-régression des valeurs décodées et benchmark synthétique de
    chargement initial.
- Out:
  - nouveaux formats BLF/MF4/MDF ;
  - cache persistant entre redémarrages serveur ;
  - remplacement de DuckDB, de `cantools` ou du frontend vanilla ;
  - export CSV/Parquet, sécurité locale et statistiques entre curseurs, déjà suivis
    par d'autres backlogs.

# Acceptance criteria
- AC1: L'import initial d'une trace avec DBC ne matérialise plus tous les signaux dans
  `samples` par défaut ; un test vérifie qu'une trace multi-signaux peut être chargée
  avec zéro ou un nombre borné de samples décodés avant toute sélection utilisateur.
- AC2: L'import conserve les informations nécessaires à la navigation : résumé, bornes
  temporelles, pagination trace, événements, IDs, statut de décodabilité, noms de
  messages connus et conflits DBC restent disponibles après chargement.
- AC3: `/api/signals` liste les signaux du DBC sans dépendre de la pré-existence de
  tous les samples ; l'indicateur de présence est dérivé des IDs présents ou marqué
  comme non encore calculé.
- AC4: `/api/series` décode uniquement le signal demandé, sur la plage demandée quand
  elle est fournie, et retourne les mêmes valeurs que l'ancien import exhaustif pour
  les fixtures existants.
- AC5: Une série déjà demandée est réutilisée depuis un cache local de session pour les
  requêtes compatibles ; un test vérifie qu'un second appel identique ne redécode pas
  les mêmes trames.
- AC6: `/api/cursor` et `/api/frame-signals` fonctionnent même si la série n'a pas été
  pré-décodée ; ils décodent le minimum nécessaire et gardent l'absence
  d'interpolation.
- AC7: Le filtre de trace par signal reste disponible ou affiche explicitement qu'il
  déclenche un décodage ciblé ; il ne force jamais le décodage global de toute la trace.
- AC8: Les erreurs de décodage, IDs inconnus, trames remote, IDs ambigus et résolutions
  DBC gardent le même sens fonctionnel qu'avant la modification.
- AC9: Un benchmark synthétique reproductible couvre import brut sans sélection et
  première demande de 1 à 8 signaux. Il publie temps d'import, temps de décodage à la
  demande, trames parcourues, samples créés et taille du cache.
- AC10: Sur le benchmark de référence avec DBC riche, le temps d'import initial est au
  moins 3 fois plus rapide que le comportement exhaustif de référence, ou l'écart est
  documenté avec une cause mesurée.
- AC11: La mémoire reste bornée pendant l'import et pendant le décodage à la demande ;
  aucun batch ne matérialise toute la trace ni tous les samples de tous les signaux en
  RAM.
- AC12: Les tests existants de pipeline, store, API et E2E restent verts après
  adaptation des attentes liées au décodage paresseux.

# AC Traceability
- request-AC1 -> This backlog slice. Proof: AC1: L'import initial d'une trace avec DBC ne matérialise plus tous les signaux dans
- request-AC2 -> This backlog slice. Proof: AC2: L'import conserve les informations nécessaires à la navigation : résumé,
- request-AC3 -> This backlog slice. Proof: AC3: `/api/signals` liste les signaux du DBC sans dépendre de la pré-existence de
- request-AC4 -> This backlog slice. Proof: AC4: `/api/series` décode uniquement le signal demandé, sur la plage demandée quand
- request-AC5 -> This backlog slice. Proof: AC5: Une série déjà demandée est réutilisée depuis un cache local de session pour les
- request-AC6 -> This backlog slice. Proof: AC6: `/api/cursor` et `/api/frame-signals` fonctionnent même si la série n'a pas été
- request-AC7 -> This backlog slice. Proof: AC7: Le filtre de trace par signal reste disponible ou affiche explicitement qu'il
- request-AC8 -> This backlog slice. Proof: AC8: Les erreurs de décodage, IDs inconnus, trames remote, IDs ambigus et résolutions
- request-AC9 -> This backlog slice. Proof: AC9: Un benchmark synthétique reproductible couvre au moins deux scénarios : import
- request-AC10 -> This backlog slice. Proof: AC10: Sur le benchmark de référence avec DBC riche, le temps d'import initial est au
- request-AC11 -> This backlog slice. Proof: AC11: La mémoire reste bornée pendant l'import et pendant le décodage à la demande ;
- request-AC12 -> This backlog slice. Proof: AC12: Les tests existants de pipeline, store, API et E2E restent verts après

# Decision framing
- Product framing: Not needed
- Product signals: (none detected)
- Product follow-up: No product brief follow-up is expected based on current signals.
- Architecture framing: Not needed
- Architecture signals: (none detected)
- Architecture follow-up: No architecture decision follow-up is expected based on current signals.

# Links
- Product brief(s): (none yet)
- Architecture decision(s): (none yet)
- Request: `logics/request/req_004_optimiser_le_chargement_des_grosses_traces_par_decodage_a_la_demande.md`
- Primary task(s): (none yet)

# AI Context
- Summary: Optimiser le chargement des grosses traces par décodage à la demande
- Keywords: backlog-groom, request, optimiser le chargement des grosses traces par décodage à la demande, bounded slice
- Use when: Use when implementing or reviewing the delivery slice for Optimiser le chargement des grosses traces par décodage à la demande.
- Skip when: Skip when the change is unrelated to this delivery slice or its linked request.

# Implementation notes
- Introduire une séparation explicite entre indexation brute et matérialisation de
  samples.
- Préserver `cantools` comme source de vérité des valeurs physiques ; le gain vient
  d'abord du fait de décoder moins de trames et de stocker moins de samples.
- Invalider le cache à chaque nouvel import, résolution DBC ou changement de catalog.
- Éviter de transformer le premier clic sur un signal en full scan non borné de toute
  la trace si l'ID de message et la plage temporelle permettent de restreindre la
  requête.

# Priority
- Priority: High
- Rationale: Les traces >100 Mo sont un cas d'usage central et le décodage exhaustif
  bloque directement le workflow opérateur ; le gain attendu sur le temps d'import est
  supérieur aux optimisations ponctuelles d'endpoint.

# Notes
- Hybrid rationale: Derived from request `req_004_optimiser_le_chargement_des_grosses_traces_par_decodage_a_la_demande` and kept bounded to one coherent delivery slice.
- Source file: `logics/request/req_004_optimiser_le_chargement_des_grosses_traces_par_decodage_a_la_demande.md`.
- Generated locally by logics-manager.
- Task `task_014_optimiser_le_chargement_des_grosses_traces_par_decodage_a_la_demande` was finished via `logics-manager flow finish task` on 2026-07-16.

# Tasks
- `task_014_optimiser_le_chargement_des_grosses_traces_par_decodage_a_la_demande`
