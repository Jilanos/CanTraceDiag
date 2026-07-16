## item_008_p0_rendre_execution_robuste_import_asynchrone_session_et_erreurs_ui - P0 Rendre l'exécution robuste import asynchrone session et erreurs UI
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
L'outil n'est pas robuste à l'exécution : l'import uploadé bloque l'event loop asyncio
pendant tout le décodage (l'API entière est gelée, y compris le polling de progression),
l'annulation d'import est factice, l'état de session est partagé sans verrou (le store
DuckDB peut être fermé et supprimé sous des requêtes concurrentes), la session précédente
est détruite avant que le nouvel import n'ait réussi, et côté UI un seul `/api/series` en
échec bloque tout le chargement sans message pendant que les autres erreurs réseau sont
avalées par des `catch` vides. Le dialog de conflit DBC peut être fermé par Échap sans
aucune issue de secours.

# Scope
- In:
  - import exécuté hors event loop (thread ou threadpool) avec progression réelle par
    phases (upload, parsing, décodage, indexation) mesurée sur octets ou trames
  - annulation effective vérifiée à chaque flush de lot, état de job cohérent
    (id renouvelé, phase `cancelled` terminale)
  - flush d'ingestion borné aussi sur `sample_batch`
  - verrouillage du cycle de vie de session : remplacement de store atomique, fermeture
    différée tant que des requêtes l'utilisent, mutations de `session.pending` protégées
  - préservation de la session précédente jusqu'au succès validé du nouvel import
  - polling de `/api/import-job` côté UI avec barre de progression et bouton Annuler
  - gestion d'erreurs UI unifiée : helper central, plus aucun `catch` vide, échec de
    série non bloquant pour le chargement, table et checkbox cohérentes, erreurs
    visibles dans une zone de statut
  - issue de secours du dialog de conflit DBC (réouverture tant que la résolution est
    en attente), état vide de la table quand les filtres ne matchent rien
- Out:
  - optimisation des endpoints chauds (curseur, pagination, index) — slice 3 de req_003
  - export, statistiques, rapport d'import — slice 4
  - sécurité locale, thème, accessibilité, responsive, dette — slices 5 à 7

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
- request-AC1 -> This backlog slice. Proof: async import with live phased progress.
- request-AC2 -> This backlog slice. Proof: effective cancellation within one batch flush.
- request-AC3 -> This backlog slice. Proof: atomic store replacement and session survival.
- request-AC4 -> This backlog slice. Proof: bounded sample_batch flush test.
- request-AC7 -> This backlog slice. Proof: unified UI error handling without empty catches.
- request-AC8 -> This backlog slice. Proof: reopenable DBC conflict dialog E2E test.

# Decision framing
- Product framing: Covered by `prod_002_product_brief_cantracediag_mvp` ; l'import
  asynchrone garde un état serveur temporaire par analyse (décision req_002 maintenue).
- Architecture framing: Covered by `adr_002_adr_architecture_cantracediag_mvp` ;
  l'import en thread doit composer avec le `RLock` existant de `TraceStore` sans
  réintroduire les instabilités corrigées par req_002.

# Links
- Product brief(s): `prod_002_product_brief_cantracediag_mvp`
- Architecture decision(s): `adr_002_adr_architecture_cantracediag_mvp`
- Request: `req_003_robustesse_execution_et_completude_post_audit_2026_07_16`
- Primary task(s): `task_008_p0_rendre_execution_robuste_import_asynchrone_session_et_erreurs_ui`

# AI Context
- Summary: Make CanTraceDiag execution robust: real async import with progress and
  cancellation, locked session lifecycle, previous-session preservation, unified UI
  error handling and a reopenable DBC conflict dialog.
- Keywords: backlog, async-import, cancellation, session-lock, error-handling,
  import-job, dbc-dialog
- Use when: Implementing the P0 execution-robustness block of req_003.
- Skip when: Work targets hot-endpoint performance, export, security or UI polish
  slices of req_003.

# Priority
- Priority: High
- Rationale: Bloc P0 de req_003 — bloquant pour l'usage réel sur traces volumineuses ;
  les audits des 15 et 16 juillet 2026 identifient ces risques comme critiques.

# Notes
- Références audit : P-01, P-02, P-05, R-01, R-05, R-06, U-01 à U-05 dans
- Task `task_008_p0_rendre_execution_robuste_import_asynchrone_session_et_erreurs_ui` was finished via `logics-manager flow finish task` on 2026-07-16.
  `docs/audit-complet-2026-07-16.md`.
- Les traces et DBC réelles restent hors dépôt ; tests sur traces synthétiques.
