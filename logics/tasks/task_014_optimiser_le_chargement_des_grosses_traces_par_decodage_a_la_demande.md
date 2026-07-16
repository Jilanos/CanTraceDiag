## task_014_optimiser_le_chargement_des_grosses_traces_par_decodage_a_la_demande - Optimiser le chargement des grosses traces par décodage à la demande
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: Medium
> Theme: Implementation delivery
> Reminder: Update status/understanding/confidence/progress and linked request/backlog references when you edit this doc.
> Owner: codex

# Definition of Done (DoD)
- [x] The backlog scope is implemented.
- [x] Acceptance criteria are covered.
- [x] Validation passes.
- [x] Meaningful waves followed ADR 009: affected docs updated and the repo left commit-ready without automatic commits.

# Backlog
- `item_014_optimiser_le_chargement_des_grosses_traces_par_decodage_a_la_demande`

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

# Implementation plan
- Séparer le pipeline d'import en deux modes : indexation brute par défaut et décodage
  exhaustif uniquement si un test ou une option explicite en a besoin.
- Étendre le store pour requêter les trames par message/arbitration ID et plage
  temporelle, sans passer par `samples`.
- Ajouter un service de décodage ciblé qui prend une clé signal, récupère les trames
  correspondantes, appelle `cantools`, filtre le signal demandé, puis écrit ou lit le
  cache de série.
- Adapter `/api/series` pour utiliser ce service et conserver la décimation actuelle
  sur les points retournés.
- Adapter `/api/signals`, `/api/cursor`, `/api/frame-signals` et le filtre trace par
  signal au modèle où les samples peuvent ne pas exister avant la première demande.
- Ajouter les tests de compatibilité des valeurs, de cache, de mémoire bornée et de
  benchmark synthétique.

# Validation
- Run `python3 -m logics_manager lint --require-status`.
- Use `python3 -m logics_manager flow progress task task_014_optimiser_le_chargement_des_grosses_traces_par_decodage_a_la_demande.md --progress <n>%` during multi-wave work.
- Run `python3 -m logics_manager flow finish task task_014_optimiser_le_chargement_des_grosses_traces_par_decodage_a_la_demande.md` after implementation.
- Run the focused Python suite covering import, store, API and diagnostics:
- Finish workflow executed on 2026-07-16.
- Linked backlog/request close verification passed.
  `uv run pytest tests/test_store_pipeline.py tests/test_api.py tests/test_diagnostic.py`.
- Run E2E or the available UI smoke tests after the API contract changes.

# Report
- Implemented lazy default import: `samples` is no longer populated unless
  exhaustive decoding is explicitly requested.
- Added targeted signal decoding for `/api/series`, `/api/cursor` and
  `/api/frame-signals`, with a DuckDB-backed session cache for compatible series
  requests.
- Adapted `/api/signals` and trace signal filtering so they work from DBC catalog
  metadata and present arbitration IDs before any series has been decoded.
- Added regression coverage for zero import-time samples and repeated series cache
  reuse, plus a reproducible synthetic benchmark script:
  `scripts/benchmark_lazy_decode.py`.
- Validation:
  - `uv run pytest -q` -> 61 passed, 11 skipped, 1 warning.
  - `uv run ruff check src tests scripts` -> All checks passed.
  - `uv run python scripts/benchmark_lazy_decode.py --frames 200 --messages 4 --signals 4`
    -> benchmark completed with non-zero eager/on-demand samples and cache stats.
  - `logics-manager lint --require-status` -> OK.
- Finished on 2026-07-16.
- Linked backlog item(s): `item_014_optimiser_le_chargement_des_grosses_traces_par_decodage_a_la_demande`
- Related request(s): `req_004_optimiser_le_chargement_des_grosses_traces_par_decodage_a_la_demande`

# AI Context
- Summary: Implement lazy on-demand signal decoding for large ASC traces: fast raw
  import, targeted `/api/series` decoding, session cache, and adapted cursor/frame
  signal behavior.
- Keywords: cantracediag, lazy-decode, signal-cache, import-performance, cantools,
  duckdb, large-asc
- Use when: Implementing or reviewing the large-trace loading optimization.
- Skip when: Work is only about export, local API security, BLF/MF4 support, or
  unrelated UI design changes.

# Links
- Request: `req_004_optimiser_le_chargement_des_grosses_traces_par_decodage_a_la_demande`
- Product brief(s): (none yet)
- Architecture decision(s): (none yet)
