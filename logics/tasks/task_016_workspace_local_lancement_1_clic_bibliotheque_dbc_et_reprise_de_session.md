## task_016_workspace_local_lancement_1_clic_bibliotheque_dbc_et_reprise_de_session - Workspace local: lancement 1-clic, bibliotheque DBC et reprise de session
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 95%
> Confidence: 85%
> Progress: 100%
> Complexity: High
> Theme: Implementation delivery
> Reminder: Update status/understanding/confidence/progress and linked request/backlog references when you edit this doc.
> Owner: claude

# Definition of Done (DoD)
- [x] The backlog scope is implemented.
- [x] Acceptance criteria are covered.
- [x] Validation passes.
- [x] Meaningful waves followed ADR 009: affected docs updated and the repo left commit-ready without automatic commits.

# Backlog
- `item_016_workspace_local_lancement_1_clic_bibliotheque_dbc_et_reprise_de_session`

# Acceptance criteria
- AC1: Un lanceur versionné permet, après une installation documentée en une
  étape par poste, de démarrer CanTraceDiag par double-clic sous Windows : le
  serveur démarre dans WSL et le navigateur Windows s'ouvre sur l'UI sans aucune
  commande tapée.
- AC2: `cantracediag serve --open` ouvre le navigateur sur l'URL effective une
  fois le serveur prêt ; sous WSL il ouvre le navigateur Windows ; hors WSL il
  utilise le mécanisme standard de la plateforme.
- AC3: Si le port demandé est occupé par un autre process, `serve` sélectionne un
  port libre et l'affiche ; si une instance CanTraceDiag répond déjà sur le port
  probé, le lanceur n'en démarre pas une seconde et ouvre le navigateur sur
  l'instance existante. Un test couvre l'auto-port ; la détection d'instance est
  couverte au moins par le probe de `/api/status`.
- AC4: Les DBC importés (upload ou chemin serveur) sont conservés dans la
  bibliothèque du workspace, dédoublonnés par hash de contenu, avec nom d'origine
  et date ; `GET /api/dbc-library` les liste. Un test vérifie le dédoublonnage et
  la présence après re-démarrage simulé.
- AC5: L'UI permet de démarrer une analyse en réutilisant des DBC de la
  bibliothèque sans nouvel upload, les DBC de la dernière session étant
  pré-sélectionnés ; le mélange bibliothèque + nouveaux fichiers fonctionne.
- AC6: Après arrêt et relance du serveur, l'UI restaure la dernière analyse via
  `/api/status` : résumé, signaux (avec sélection localStorage), graphes, vue
  trace et résolution de conflits appliquée, sans ré-import ni re-parse de l'ASC.
  Un test redémarre l'app (nouvelle instance de l'API sur le même workspace) et
  vérifie la restauration.
- AC7: Si le manifest ou le DuckDB de la dernière analyse est absent, corrompu ou
  incohérent (hash/DBC manquant), le serveur démarre proprement sur un état vide
  avec un message clair ; aucun crash au démarrage.
- AC8: La bibliothèque respecte un cap LRU configurable (défaut documenté) et une
  action de purge supprime DBC en cache et dernière analyse ; un test couvre
  l'éviction LRU et la purge.
- AC9: Toutes les données du workspace restent sous le répertoire de données
  utilisateur, jamais dans le dépôt ; le chemin est surchargeable par variable
  d'environnement (utile aux tests) ; la suite de tests n'écrit pas dans le
  profil réel de l'utilisateur.
- AC10: Le mode éphémère reste disponible et documenté ; avec lui, le
  comportement actuel (tempdir, rien ne survit) est inchangé.
- AC11: `ruff check .` et `pytest` restent verts, E2E Playwright inclus ; le
  README documente le lanceur, l'installation du raccourci et le workspace
  (emplacement, purge, mode éphémère).

# Implementation plan
- Wave 1 — Module workspace : créer `src/cantracediag/workspace.py` (résolution
  du répertoire de données XDG avec surcharge par env var `CANTRACEDIAG_DATA_DIR`,
  manifest JSON versionné, hash de contenu, éviction LRU, purge, mode éphémère) ;
  fixtures de tests pointant le workspace vers un tmpdir ; ADR court consignant
  la disposition (emplacement, manifest, LRU/purge, éphémère).
- Wave 2 — Bibliothèque DBC : alimenter la bibliothèque à chaque import (upload
  et chemin serveur), dédup par hash avec nom d'origine et date d'usage ;
  `GET /api/dbc-library`, endpoint de purge ; tests dédoublonnage, LRU,
  présence après redémarrage simulé (AC4, AC8).
- Wave 3 — Persistance de session : remplacer les `tempfile.mkdtemp` d'`api.py`
  par le workspace (nouveau DuckDB écrit à côté puis bascule atomique pour
  préserver la sémantique transactionnelle req_003) ; écrire le manifest à
  chaque analyse finalisée (trace, DBC hashés, base ASC, résolution) ;
  rechargement au démarrage avec validation (version de schéma, fichiers
  présents) et repli propre sur état vide (AC6, AC7, AC9, AC10).
- Wave 4 — UI bibliothèque : panneau « DBC library » dans le flux d'import
  (liste avec nom/date, pré-sélection des DBC de la dernière session, mélange
  avec de nouveaux uploads), action « vider le cache », états d'erreur visibles ;
  conformité charte `docs/design-ui.md` (AC5).
- Wave 5 — CLI et lanceur : `serve --open` (détection WSL → `explorer.exe` ou
  `wslview`, sinon `webbrowser` ; best-effort, jamais bloquant), auto-port si
  occupé, probe `/api/status` avant démarrage ; `scripts/CanTraceDiag.cmd` +
  `scripts/install-shortcut.ps1` (raccourci généré avec le chemin réel du
  dépôt) ; test auto-port (AC1, AC2, AC3).
- Wave 6 — Finalisation : README (installation par poste, workspace, purge,
  mode éphémère), test E2E de restauration si Chromium disponible, passe
  complète `ruff` + `pytest` + E2E, mise à jour des docs Logics (AC11).

# Validation
- Run `python3 -m logics_manager lint --require-status`.
- Use `python3 -m logics_manager flow progress task task_016_workspace_local_lancement_1_clic_bibliotheque_dbc_et_reprise_de_session.md --progress <n>%` during multi-wave work.
- Run `python3 -m logics_manager flow finish task task_016_workspace_local_lancement_1_clic_bibliotheque_dbc_et_reprise_de_session.md` after implementation.
- `.venv/bin/ruff check .` et `.venv/bin/pytest` verts, E2E Playwright inclus.
- Test de reprise : lancer l'API sur un workspace de test, importer une fixture,
- Finish workflow executed on 2026-07-16.
- Linked backlog/request close verification passed.
  détruire l'instance, en créer une nouvelle sur le même workspace, vérifier que
  `/api/status` restaure l'analyse sans ré-import.
- Vérification AC9 : lancer la suite de tests puis contrôler qu'aucun fichier
  n'a été créé sous le vrai `~/.local/share/cantracediag/`.
- Smoke test manuel double-clic sur un poste Windows : installation du
  raccourci, premier lancement, second lancement (instance déjà active),
  redémarrage machine puis relance (reprise de session).

# Report
- Workspace local persistant livré ; structure et comportements existants
- Finished on 2026-07-16.
- Linked backlog item(s): `item_016_workspace_local_lancement_1_clic_bibliotheque_dbc_et_reprise_de_session`
- Related request(s): `req_006_workspace_local_lancement_1_clic_bibliotheque_dbc_et_reprise_de_session`
  préservés (mode éphémère par défaut en test).
- `src/cantracediag/workspace.py` (nouveau) : résolution du répertoire XDG avec
  surcharge `CANTRACEDIAG_DATA_DIR`, mode éphémère (`CANTRACEDIAG_EPHEMERAL`),
  bibliothèque DBC dédupliquée par hash (`dbc/<digest>/<nom>` + `index.json`),
  éviction LRU (`CANTRACEDIAG_DBC_CAP`, défaut 20) + prune des orphelins, purge,
  holders d'analyse (`analysis/<uuid>/analysis.duckdb`), manifest versionné
  (`SCHEMA_VERSION`) avec écriture atomique.
- `src/cantracediag/api.py` : `create_app(workspace=None)` ; holders via le
  workspace ; `_finalize` alimente la bibliothèque et commit le manifest
  (best-effort) ; `_restore_last_analysis()` au démarrage (réouverture DuckDB +
  rechargement des DBC de bibliothèque, repli propre si absent/corrompu/incohérent) ;
  `/api/import-files` accepte un champ `library` (digests) ; nouveaux endpoints
  `GET /api/dbc-library` et `POST /api/workspace-purge` ; session exposée sur
  `app.state.ctd_session`.
- `src/cantracediag/cli.py` : `serve --open` (ouverture navigateur Windows depuis
  WSL via `explorer.exe`/`wslview`, best-effort), auto-port si occupé, détection
  d'instance (`resolve_serve_target`, probe `/api/status`).
- `scripts/CanTraceDiag.cmd` + `scripts/install-shortcut.ps1` : lanceur
  double-clic Windows/WSL, raccourci Bureau généré avec le chemin réel du dépôt.
- UI (`web/index.html`, `web/app.js`) : bouton **Library** + dialogue (liste,
  pré-sélection des DBC de la dernière session, action **Clear cache**),
  digests joints au FormData de load, chargement de la bibliothèque à l'init et
  après import ; conforme à la charte design-ui.
- `docs/adr/0006-workspace-local-persistant.md` + section README (lanceur 1-clic,
  workspace, purge, mode éphémère, nouveaux endpoints).
- Tests : `tests/conftest.py` force le mode éphémère (AC9) ;
  `tests/test_workspace.py` (dédup, LRU, purge, éphémère, reprise après
  redémarrage, manifest corrompu, DBC manquant, réutilisation bibliothèque) ;
  `tests/test_cli.py` (auto-port).
- Validation :
  - `.venv/bin/ruff check .` -> All checks passed.
  - `.venv/bin/pytest -q` -> 82 passed, 1 warning (dont 11 E2E Playwright avec
    Chromium ; l'UI Library n'a rien cassé, y compris le test viewport 390 px).
  - AC9 vérifié : aucun fichier créé sous le vrai `~/.local/share/cantracediag/`.
  - Smoke test live : import -> bibliothèque alimentée + manifest écrit ->
    reprise après « redémarrage » (nouvelle app même workspace) -> purge.
- Limite : le smoke test manuel double-clic reste à faire par l'opérateur sur un
  poste Windows (non automatisable dans cet environnement).

# AI Context
- Summary: Implement the persistent local workspace: XDG data dir with env
  override, content-hashed DBC library with LRU and purge, last-analysis
  restore across restarts (DuckDB + versioned manifest, transactional swap),
  UI library panel, and one-click Windows/WSL launcher with serve --open,
  auto-port and instance probe.
- Keywords: cantracediag, workspace, launcher, wsl, dbc-library,
  session-restore, duckdb-persistence, lru, serve-open, xdg
- Use when: Implementing or reviewing the local workspace task.
- Skip when: Work targets decoding accuracy, trace formats, export, timing
  analysis, or unrelated UI features.

# Links
- Request: `req_006_workspace_local_lancement_1_clic_bibliotheque_dbc_et_reprise_de_session`
- Product brief(s): (none yet)
- Architecture decision(s): `docs/adr/0004-donnees-locales-hors-depot.md`
