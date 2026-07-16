## req_006_workspace_local_lancement_1_clic_bibliotheque_dbc_et_reprise_de_session - Workspace local: lancement 1-clic, bibliotheque DBC et reprise de session
> From version: 1.0.0
> Schema version: 1.0
> Status: Draft
> Understanding: Supprimer la friction quotidienne d'usage sur poste Windows+WSL : démarrer CanTraceDiag par un double-clic (raccourci Windows + serve intelligent) et retrouver au lancement la dernière analyse (bibliothèque DBC côté serveur, session persistante hors tempdir) sans re-sélectionner ni re-uploader les fichiers.
> Confidence: high
> Complexity: medium
> Theme: operator-workflow
> Reminder: Update status/understanding/confidence and linked backlog/task references when you edit this doc.

# Needs
- Lancer CanTraceDiag depuis Windows en un double-clic sur les deux postes de
  l'opérateur (perso et travail, tous deux Windows + WSL), sans ouvrir de terminal
  ni taper de commande : le serveur démarre dans WSL et le navigateur Windows
  s'ouvre sur l'UI.
- Rendre le lancement idempotent : si une instance tourne déjà, le double-clic ne
  relance pas un second serveur, il rouvre simplement le navigateur sur l'instance
  existante ; si le port par défaut est occupé par un autre process, le serveur en
  choisit un libre au lieu d'échouer.
- Éviter de re-sélectionner et re-téléverser les DBC à chaque session : les DBC
  déjà importés sont conservés côté serveur dans un cache local et proposés à la
  réutilisation dans l'UI, ceux de la dernière session étant pré-sélectionnés.
- Retrouver la dernière analyse au démarrage : après un redémarrage du serveur (ou
  du PC), rouvrir l'UI restaure la dernière trace indexée, ses DBC, la résolution
  de conflits appliquée et les préférences locales existantes (signaux cochés,
  filtres, colonnes) sans ré-import.
- Garder toutes les données réelles hors dépôt et locales au profil utilisateur,
  conformément à l'ADR 0004, avec un moyen simple de purger le cache.

# Context
- Aujourd'hui le lancement demande ~4 actions : ouvrir un terminal WSL, se placer
  dans le dépôt, activer/pointer le venv, lancer `cantracediag serve`, puis ouvrir
  manuellement le navigateur. `serve` (`src/cantracediag/cli.py:50`) n'a ni
  ouverture navigateur, ni auto-port, ni détection d'instance.
- La session API est éphémère : `api.py` écrit le DuckDB d'analyse et les DBC
  uploadés dans des répertoires `tempfile.mkdtemp` (`api.py:417`, `api.py:693`).
  Au redémarrage du serveur, tout est perdu ; le navigateur ne pouvant pas relire
  des fichiers locaux sans geste utilisateur, l'opérateur re-téléverse trace et
  DBC à chaque session.
- Le frontend persiste déjà en localStorage la sélection de signaux, les filtres,
  les colonnes et la disposition ; `/api/status` sait déjà restaurer une session
  active côté client (`app.js`, `init()`). Il manque uniquement la persistance
  côté serveur pour que cette restauration survive à un redémarrage.
- `wsl.exe -e` permet de lancer une commande dans la distro par défaut depuis
  Windows sans terminal interactif ; `explorer.exe <url>` (ou `wslview`) ouvre le
  navigateur Windows depuis WSL. Un lanceur `.cmd` versionné + un flag `--open`
  suffisent donc à un vrai 1-clic sans dépendance nouvelle.
- Les DBC changent rarement et sont petits ; un cache indexé par hash de contenu
  dédoublonne naturellement les re-imports. Les traces, elles, sont volumineuses :
  la reprise de session doit rouvrir l'index DuckDB existant, pas re-parser l'ASC.

# Product decisions
- Lancement : livrer un lanceur Windows versionné (`scripts/CanTraceDiag.cmd` +
  script d'installation de raccourci PowerShell) et enrichir `cantracediag serve`
  avec `--open` (ouverture du navigateur Windows depuis WSL), auto-port en cas de
  port occupé et détection d'instance via probe de `/api/status`. Pas de packaging
  Windows natif ni de service systemd dans cette requête.
- Workspace : introduire un répertoire de données utilisateur (`XDG data home`,
  par défaut `~/.local/share/cantracediag/`) contenant la bibliothèque DBC
  (`dbc/`, fichiers indexés par hash de contenu avec nom d'origine et date) et la
  dernière analyse (`last-analysis.duckdb` + manifest JSON : trace, DBC, base ASC,
  résolution de conflits, horodatage).
- L'import web continue d'accepter les uploads ; chaque DBC uploadé alimente la
  bibliothèque. L'UI expose la bibliothèque (`GET /api/dbc-library`) et permet de
  composer une session avec un mélange de DBC en bibliothèque et de nouveaux
  uploads ; les DBC de la dernière session sont pré-sélectionnés.
- Reprise : au démarrage, le serveur recharge la dernière analyse si le manifest
  et le fichier DuckDB sont présents et cohérents ; `/api/status` la présente
  comme session active. Une nouvelle analyse remplace la précédente (une seule
  « dernière analyse » dans cette requête, pas de multi-sessions nommées).
- Bibliothèque bornée : cap LRU (valeur par défaut ~20 DBC) et endpoint/action UI
  de purge (« vider le cache ») couvrant DBC et dernière analyse.
- La désactivation reste possible : un flag (`--ephemeral` ou équivalent) conserve
  le comportement actuel en tempdir pour les tests et les usages jetables ; les
  tests existants ne doivent pas se mettre à écrire dans le profil utilisateur.

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

# Suggested implementation slices
- Slice 1: Module workspace (résolution du répertoire de données, surcharge par
  env var, manifest JSON, utilitaires hash/LRU/purge) + bascule des imports de
  `tempfile.mkdtemp` vers le workspace avec flag éphémère.
- Slice 2: Bibliothèque DBC : alimentation à l'import, `GET /api/dbc-library`,
  endpoint de purge, éviction LRU, tests dédiés.
- Slice 3: Reprise de session : écriture du manifest à chaque analyse finalisée,
  rechargement au démarrage, `/api/status` enrichi, gestion des états corrompus,
  test de redémarrage.
- Slice 4: UI : panneau « bibliothèque DBC » dans le flux d'import (liste,
  pré-sélection dernière session, mélange avec uploads), action purge, états
  d'erreur visibles, conformité charte design-ui.
- Slice 5: CLI et lanceur : `serve --open` + auto-port + probe d'instance,
  `scripts/CanTraceDiag.cmd`, `scripts/install-shortcut.ps1`, documentation
  README pour l'installation sur un poste neuf.

# Out of scope
- Packaging Windows natif (PyInstaller/MSI) et exécution hors WSL ; service
  systemd ou démarrage automatique avec Windows.
- Sessions multiples nommées, historique d'analyses ou comparaison de traces ;
  une seule « dernière analyse » est conservée.
- Cache des traces ASC elles-mêmes (seul l'index DuckDB de la dernière analyse
  est conservé) ; support BLF/MF4.
- Synchronisation du workspace entre les deux postes (chaque poste a son cache).
- Toute évolution des fonctions d'analyse (export, statistiques, recherche par
  condition), couvertes par d'autres requêtes.

# Definition of Ready (DoR)
- [x] Problem statement is explicit and user impact is clear.
- [x] Scope boundaries (in/out) are explicit.
- [x] Acceptance criteria are testable.
- [x] Dependencies and known risks are listed.

# Dependencies and risks
- Le remplacement des tempdirs touche le cycle de vie de la session dans
  `api.py` (verrou `_lock`, `replace_store`, annulation d'import) : la migration
  doit préserver la sémantique transactionnelle durcie par req_003 (le store
  précédent reste intact jusqu'au succès du nouveau).
- Réouvrir un DuckDB écrit par une version antérieure du schéma peut échouer :
  le manifest doit porter une version de schéma et invalider proprement plutôt
  que planter (AC7).
- La détection « WSL vs Linux natif » pour `--open` (choix `explorer.exe` /
  `wslview` / `webbrowser`) doit être robuste et silencieusement dégradable :
  l'échec d'ouverture du navigateur ne doit jamais empêcher le serveur de
  démarrer.
- Le lanceur `.cmd` dépend du chemin du dépôt sur chaque poste : le script
  d'installation doit générer le raccourci avec le bon chemin plutôt que de le
  coder en dur.
- Risque de fuite d'espace disque : le cap LRU et la purge doivent couvrir les
  fichiers orphelins (DBC référencés par aucun manifest).
- Les tests actuels supposent l'isolation tempdir ; AC9 impose une env var de
  surcharge du workspace consommée par les fixtures pour éviter toute écriture
  dans le profil réel.

# Companion docs
- Product brief(s): (none yet)
- Architecture decision(s): `docs/adr/0004-donnees-locales-hors-depot.md` (contrainte respectée)

# References
- `src/cantracediag/cli.py`
- `src/cantracediag/api.py`
- `src/cantracediag/store.py`
- `src/cantracediag/web/app.js`
- `src/cantracediag/web/index.html`
- `tests/test_api.py`
- `tests/test_e2e_ui.py`
- `docs/adr/0004-donnees-locales-hors-depot.md`
- `logics/request/req_003_robustesse_execution_et_completude_post_audit_2026_07_16.md`

# AI Context
- Summary: Deliver a persistent local workspace for CanTraceDiag on Windows+WSL:
  one-click launcher (.cmd + serve --open with auto-port and instance probe),
  server-side DBC library deduplicated by content hash, and last-analysis
  restore across server restarts (DuckDB + manifest), with LRU cap, purge and an
  ephemeral fallback mode.
- Keywords: cantracediag, workspace, launcher, wsl, one-click, dbc-cache,
  dbc-library, session-restore, duckdb-persistence, lru, serve-open
- Use when: Implementing or reviewing the launcher, DBC library, session
  persistence, or workspace storage layout.
- Skip when: Work targets decoding accuracy, trace formats (BLF/MF4), export,
  timing analysis, or UI features unrelated to import/session lifecycle.

# Backlog
- none
- `item_016_workspace_local_lancement_1_clic_bibliotheque_dbc_et_reprise_de_session`
