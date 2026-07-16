## task_008_p0_rendre_execution_robuste_import_asynchrone_session_et_erreurs_ui - P0 Rendre l'exécution robuste import asynchrone session et erreurs UI
> From version: 1.0.0
> Schema version: 1.0
> Status: Ready
> Understanding: 90%
> Confidence: 85%
> Progress: 0%
> Complexity: High
> Theme: Implementation delivery
> Reminder: Update status/understanding/confidence/progress and linked request/backlog references when you edit this doc.

# Context
- Livrer le bloc P0 de req_003 : import asynchrone réel avec progression et annulation
  effective, cycle de vie de session verrouillé, préservation de la session précédente,
  gestion d'erreurs UI unifiée et dialog de conflit DBC rouvrable.
- Constats sources : P-01, P-02, P-05, R-01, R-05, R-06, U-01 à U-05 de
  `docs/audit-complet-2026-07-16.md`.

# Plan
- [ ] 1. Backend — import hors event loop : exécuter `_prepare`/`import_trace` dans un
  thread (ou `run_in_threadpool`), passer un callback de progression (octets/trames
  traités par phase) et un `threading.Event` d'annulation vérifié à chaque flush de
  lot ; renouveler l'id de job à chaque import ; rendre `cancelled` terminal.
- [ ] 2. Backend — borner `sample_batch` dans la condition de flush du pipeline
  (`pipeline.py:87`) avec test d'ingestion multi-signaux.
- [ ] 3. Backend — verrou de cycle de vie de session : mutations de `Session` sous
  lock, remplacement de store atomique avec fermeture différée (compteur de requêtes en
  cours ou close-quand-idle) ; ne détruire l'ancienne session qu'après succès validé du
  nouvel import (déplacer le `clear_store` de `_preview_unresolved`).
- [ ] 4. Frontend — polling de `/api/import-job` (~500 ms) pendant l'indexation :
  alimenter `#progressBar` par phase et afficher un bouton Annuler appelant
  `/api/import-cancel`.
- [ ] 5. Frontend — helper d'erreurs central (journalisation console + zone de statut
  UI) : remplacer tous les `catch (_) {}`, passer `restoreSelected` en
  `Promise.allSettled` avec marquage par entrée, protéger `loadTrace`/`toggleSignal`
  (checkbox et table cohérentes), normaliser `detail` non textuel des 422.
- [ ] 6. Frontend — dialog de conflit DBC : gérer l'événement `cancel` et afficher un
  contrôle « Résoudre les conflits » persistant tant que la session est en attente ;
  état vide de la table quand aucun résultat.
- [ ] 7. Tests : progression pendant import synthétique (AC1), annulation effective
  (AC2), rafales concurrentes pendant remplacement de store + survie de session (AC3),
  flush borné (AC4), échec de série non bloquant (AC5), E2E dialog rouvrable (AC6).
- [ ] GATE: do not close a wave or step until the relevant automated tests and quality
  checks have been run successfully.

# Backlog
- `item_008_p0_rendre_execution_robuste_import_asynchrone_session_et_erreurs_ui`

# Definition of Done (DoD)
- [ ] Code is implemented and reviewed.
- [ ] Validation passes.
- [ ] Linked docs are synchronized.
- [ ] Meaningful waves followed ADR 009: affected docs updated and the repo left commit-ready without automatic commits.

# Acceptance criteria
- AC1: Pendant l'import d'une trace volumineuse, `/api/import-job` répond en moins de
  200 ms, expose des phases et une progression mesurée sur les octets ou trames
  traités ; un test le prouve avec une trace synthétique.
- AC2: L'annulation interrompt réellement le pipeline en moins d'un flush de lot,
  laisse la session dans un état cohérent et se reflète dans l'UI ; un job annulé
  n'est plus déclaré annulable.
- AC3: Un import qui échoue ou est annulé laisse la session précédente intacte et
  interrogeable ; le remplacement de store est atomique et aucun test de rafale
  concurrente ne produit d'erreur de connexion fermée.
- AC4: `sample_batch` est borné par la même limite de lot que frames et événements ;
  un test d'ingestion avec un message multi-signaux le vérifie.
- AC5: L'échec d'un `/api/series` au chargement ou au toggle n'empêche ni le rendu du
  plot ni la table ; l'erreur est visible dans l'UI, la checkbox reste cohérente, et
  plus aucun `catch` vide ne subsiste dans `app.js`.
- AC6: Le dialog de conflit DBC fermé par Échap peut être rouvert par un contrôle
  visible tant que la résolution est en attente ; testé en E2E.

# AC Traceability
- request-AC1 -> This task. Proof: async import with phased progress and responsive job endpoint test.
- request-AC2 -> This task. Proof: cancellation event checked at each batch flush, terminal state test.
- request-AC3 -> This task. Proof: locked session lifecycle, concurrent-burst test without closed-connection errors.
- request-AC4 -> This task. Proof: bounded sample_batch flush with multi-signal ingestion test.
- request-AC7 -> This task. Proof: central error helper, allSettled restore, no empty catch in app.js.
- request-AC8 -> This task. Proof: E2E test reopening the DBC conflict dialog after Escape.
- backlog-AC1..AC6 -> This task. Proof: one-to-one implementation of the backlog acceptance criteria.

# Validation
- Run `python3 -m logics_manager lint --require-status`.
- Use `python3 -m logics_manager flow progress task task_008_p0_rendre_execution_robuste_import_asynchrone_session_et_erreurs_ui.md --progress <n>%` during multi-wave work.
- Run `python3 -m logics_manager flow finish task task_008_p0_rendre_execution_robuste_import_asynchrone_session_et_erreurs_ui.md` after implementation.
- `.venv/bin/ruff check .` must pass.
- `.venv/bin/pytest` must pass, including the new AC1-AC6 tests and existing E2E.

# Report
- (pending implementation)

# AI Context
- Summary: Implement the req_003 P0 block: real async import with progress and
  cancellation, locked session lifecycle with previous-session preservation, unified UI
  error handling and a reopenable DBC conflict dialog.
- Keywords: task, async-import, cancellation, session-lock, error-handling, e2e
- Use when: Executing the P0 execution-robustness slice of req_003.
- Skip when: Work targets later req_003 slices (hot endpoints, export, security, UI
  polish, debt).

# Links
- Request: `req_003_robustesse_execution_et_completude_post_audit_2026_07_16`
- Product brief(s): `prod_002_product_brief_cantracediag_mvp`
- Architecture decision(s): `adr_002_adr_architecture_cantracediag_mvp`
