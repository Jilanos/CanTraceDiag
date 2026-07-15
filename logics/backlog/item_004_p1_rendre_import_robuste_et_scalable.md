## item_004_p1_rendre_import_robuste_et_scalable - P1 Rendre import robuste et scalable
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
Les imports volumineux restent trop dépendants de la mémoire vive et n'exposent pas assez
de progression, d'annulation ni de sémantique transactionnelle pour un atelier local qui
manipule des traces de 40 à 150 Mo avec DBC.

# Scope
- In:
  - stockage DuckDB/cache temporaire sur disque hors dépôt
  - optimisation mesurée au maximum raisonnable pour une trace cible 150 Mo avec DBC
  - job d'import côté serveur avec phases, progression et annulation
  - état serveur temporaire suffisant pour l'atelier local, sans persistance durable des
    jobs après redémarrage
  - erreurs métier déterministes pour DBC invalide, résolution inconnue/incomplète,
    basenames identiques et payload tronqué
  - conservation de la session précédente jusqu'au succès validé du nouvel import
- Out:
  - stockage cloud ou collaboration multi-utilisateur
  - garantie de performance absolue indépendante de la machine
  - support complet de reprise de job après redémarrage serveur

# Acceptance criteria
- AC6: Le stockage d'une analyse volumineuse utilise un fichier DuckDB/cache temporaire
  hors dépôt et ne dépend plus d'une base complète en mémoire.
- AC7: Une trace réelle ou synthétique représentative de 150 Mo avec DBC fait l'objet
  d'une optimisation au maximum raisonnable et d'un budget documenté de temps/mémoire ; la
  CI protège au moins un budget synthétique réduit et reproductible.
- AC8: L'import expose des phases et une progression mesurable, peut être annulé, retourne
  des erreurs actionnables, continue en arrière-plan pour les frames non ambiguës et ne
  détruit la session précédente qu'après succès validé.
- AC9: Une DBC invalide, une résolution incomplète/inconnue, deux basenames identiques et
  un payload tronqué ont des comportements déterministes, visibles et testés.

# AC Traceability
- request-AC6 -> This backlog slice. Proof: disk-backed DuckDB/cache for large analyses.
- request-AC7 -> This backlog slice. Proof: documented best-effort performance budget.
- request-AC8 -> This backlog slice. Proof: cancellable temporary import jobs and safe session commit.
- request-AC9 -> This backlog slice. Proof: deterministic business errors for known edge cases.
- request-AC1 -> This backlog slice. Evidence needed: Tout arbitration ID défini par plusieurs DBC est détecté, y compris lorsque le nom
- request-AC2 -> This backlog slice. Evidence needed: Toute résolution DBC est exhaustive, validée contre les choix disponibles,
- request-AC3 -> This backlog slice. Evidence needed: L'ordre de sélection ou d'upload des DBC ne change jamais silencieusement les
- request-AC4 -> This backlog slice. Evidence needed: Les noms, unités, valeurs et détails provenant des ASC/DBC sont rendus comme texte,
- request-AC5 -> This backlog slice. Evidence needed: La CI installe les extras nécessaires depuis un environnement propre et exécute
- request-AC10 -> This backlog slice. Evidence needed: La vue trace filtre côté serveur par signal en combinaison avec temps, ID, message,
- request-AC11 -> This backlog slice. Evidence needed: La recherche de signaux couvre message, signal, ID, unité et DBC, et permet de
- request-AC12 -> This backlog slice. Evidence needed: Les colonnes pertinentes proposent les formats attendus (temps, hexadécimal,
- request-AC13 -> This backlog slice. Evidence needed: Aucun contrôle principal ne sort du viewport à 1280x720, 1024x768 et 390x844 ; à
- request-AC14 -> This backlog slice. Evidence needed: Le graphe et les commandes critiques ont des noms accessibles, un focus visible et
- request-AC15 -> This backlog slice. Evidence needed: Les états vide, chargement et erreur guident l'opérateur sans texte permanent de
- request-AC16 -> This backlog slice. Evidence needed: README, roadmap et ADR distinguent clairement l'implémentation livrée de la cible,

# Delivery notes
- Recommandation retenue : jobs d'import temporaires en mémoire serveur, identifiés par
  analyse, suffisants pour progression et annulation dans une session locale.
- Mesurer avant/après sur données synthétiques reproductibles et documenter la machine de
  référence lorsque des traces réelles hors dépôt sont utilisées manuellement.

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
- Request: `req_002_fiabiliser_cantracediag_apres_audit_fonctionnel_ui_et_performance`
- Primary task(s): `task_004_p1_rendre_import_robuste_et_scalable`

# AI Context
- Summary: Move large imports to disk-backed storage with cancellable temporary jobs,
  deterministic errors and documented best-effort performance budgets.
- Keywords: backlog-groom, request, p1 rendre import robuste et scalable, bounded slice
- Use when: Use when implementing or reviewing the delivery slice for P1 Rendre import robuste et scalable.
- Skip when: Skip when the change is unrelated to this delivery slice or its linked request.

# Priority
- Priority: Medium
- Rationale: La cible de 150 Mo est atteinte sans DBC mais le pic mémoire du décodage
  impose ce lot avant l'élargissement des usages.

# Notes
- Hybrid rationale: Derived from request `req_002_fiabiliser_cantracediag_apres_audit_fonctionnel_ui_et_performance` and kept bounded to one coherent delivery slice.
- Source file: `logics/request/req_002_fiabiliser_cantracediag_apres_audit_fonctionnel_ui_et_performance.md`.
- Generated locally by logics-manager.
- Task `task_004_p1_rendre_import_robuste_et_scalable` was finished via `logics-manager flow finish task` on 2026-07-15.

# Tasks
- `task_004_p1_rendre_import_robuste_et_scalable`
