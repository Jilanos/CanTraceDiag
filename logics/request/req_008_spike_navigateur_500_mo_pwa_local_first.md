## req_008_spike_navigateur_500_mo_pwa_local_first - Spike navigateur 500 Mo pour PWA local-first
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Complexity: Medium
> Theme: General
> Reminder: Update status/understanding/confidence and linked backlog/task references when you edit this doc.

# Needs
- Prouver ou invalider la capacité d'une PWA local-first à lire et scanner des
  traces ASC volumineuses directement dans un navigateur desktop, sans backend
  Python et sans charger tout le fichier en mémoire.
- Produire une preuve mesurée avant toute migration du parser ASC, du moteur DBC
  ou de l'UI vers une architecture entièrement locale au navigateur.
- Faire de ce spike le jalon 0.1 de la roadmap
  `road_001_architecture_pwa_spa_local_first`.

# Context
- La roadmap PWA/SPA local-first est conditionnée à un premier jalon de
  faisabilité sur fichiers potentiellement gros. Des traces ASC de 500 Mo sont
  rares mais possibles ; le navigateur doit les parcourir par chunks et jeter les
  données intermédiaires au lieu de les convertir en millions d'objets retenus.
- Le moteur Python actuel lit déjà les ASC en streaming et indexe par lots. Le
  spike doit vérifier si un navigateur peut reproduire la partie lecture/scanner
  avec `File.slice()`, `TextDecoder` streaming et Web Worker.
- Le résultat attendu n'est pas encore un diagnostic complet. Il s'agit d'un
  go/no-go technique : si le navigateur échoue sur la lecture chunkée, la suite
  doit pivoter vers une architecture serveur multi-session.

# Acceptance criteria
- AC1: Une branche `feat/pwa-local-first` existe ou est explicitement utilisée
  pour isoler le spike du flux principal.
- AC2: Le spike lit un fichier ASC via `File.slice()` par chunks configurables,
  sans appeler de backend applicatif.
- AC3: Le parsing s'exécute dans un Web Worker et l'UI reste responsive pendant
  l'import, avec progression et annulation.
- AC4: Les lignes coupées entre deux chunks sont reconstruites correctement et
  couvertes par au moins un test ou fixture dédié.
- AC5: Les mesures couvrent au minimum 50 Mo et 150 Mo ; 500 Mo est mesuré dès
  qu'une fixture locale représentative est disponible.
- AC6: Le rapport de sortie documente temps de scan, taille de chunk retenue,
  observations mémoire, limites navigateur et décision go/no-go pour le jalon
  0.2.

# Definition of Ready (DoR)
- [x] Problem statement is explicit and user impact is clear.
- [x] Scope boundaries (in/out) are explicit.
- [x] Acceptance criteria are testable.
- [x] Dependencies and known risks are listed.

# Companion docs
- Product brief(s): (none yet)
- Architecture decision(s): (none yet)
- Roadmap(s): `road_001_architecture_pwa_spa_local_first`

# References
- `logics/roadmap/road_001_architecture_pwa_spa_local_first.md`
- `src/cantracediag/pipeline.py`
- `src/cantracediag/formats/asc.py`

# AI Context
- Summary: Request for the roadmap 0.1 feasibility spike: browser-side chunked
  reading and scanning of large ASC files up to a possible 500 MB target before
  continuing the PWA/local-first migration.
- Keywords: request-draft, pwa, spa, local-first, spike, asc, 500 mb, chunks,
  file.slice, textdecoder, web worker, memory
- Use when: Starting or reviewing the first PWA/local-first milestone.
- Skip when: Implementing full ASC/DBC parity or static deployment after the
  feasibility decision.

# Backlog
- `item_018_spike_navigateur_500_mo_pour_pwa_local_first`
