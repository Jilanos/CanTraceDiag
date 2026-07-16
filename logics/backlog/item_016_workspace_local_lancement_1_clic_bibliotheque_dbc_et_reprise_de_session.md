## item_016_workspace_local_lancement_1_clic_bibliotheque_dbc_et_reprise_de_session - Workspace local: lancement 1-clic, bibliotheque DBC et reprise de session
> From version: 1.0.0
> Schema version: 1.0
> Status: Ready
> Understanding: 95%
> Confidence: 85%
> Progress: 0%
> Complexity: High
> Theme: Operator workflow and runtime integration
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
Le lancement quotidien demande ~4 actions manuelles dans un terminal WSL et la
session est intégralement éphémère (`tempfile.mkdtemp` dans `api.py`) : à chaque
redémarrage du serveur, l'opérateur re-sélectionne et re-téléverse trace et DBC
depuis le navigateur alors que les DBC changent rarement.

Ce backlog livre le « workspace local » : lancement en un double-clic Windows
(lanceur versionné + `serve --open` avec auto-port et détection d'instance),
bibliothèque DBC persistante côté serveur (dédup par hash, pré-sélection de la
dernière session) et reprise de la dernière analyse au démarrage (DuckDB +
manifest, sans re-parse de l'ASC), le tout hors dépôt conformément à l'ADR 0004.

# Scope
- In:
  - module workspace : répertoire de données utilisateur (XDG, surcharge par env
    var), manifest JSON versionné, utilitaires hash/LRU/purge, flag éphémère
    conservant le comportement tempdir actuel ;
  - bibliothèque DBC : alimentation à l'import (upload et chemin serveur),
    `GET /api/dbc-library`, éviction LRU, endpoint et action UI de purge ;
  - reprise de session : `last-analysis.duckdb` + manifest écrits à chaque
    analyse finalisée, rechargement au démarrage, `/api/status` enrichi, gestion
    propre des états absents/corrompus ;
  - UI : panneau bibliothèque DBC dans le flux d'import (liste, pré-sélection
    dernière session, mélange bibliothèque + uploads), conforme à la charte
    `docs/design-ui.md` ;
  - CLI/lanceur : `serve --open` (navigateur Windows depuis WSL), auto-port,
    probe d'instance, `scripts/CanTraceDiag.cmd`, `scripts/install-shortcut.ps1`,
    documentation README.
- Out:
  - packaging Windows natif, exécution hors WSL, service systemd/autostart ;
  - sessions multiples nommées, historique d'analyses, comparaison de traces ;
  - cache des traces ASC elles-mêmes ; support BLF/MF4 ;
  - synchronisation du workspace entre postes ;
  - fonctions d'analyse (export, statistiques, recherche par condition), suivies
    par d'autres requêtes.

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

# AC Traceability
- request-AC1 -> This backlog slice. Proof: AC1 (lanceur double-clic Windows/WSL).
- request-AC2 -> This backlog slice. Proof: AC2 (serve --open multi-plateforme).
- request-AC3 -> This backlog slice. Proof: AC3 (auto-port + détection d'instance).
- request-AC4 -> This backlog slice. Proof: AC4 (bibliothèque DBC hashée + API).
- request-AC5 -> This backlog slice. Proof: AC5 (réutilisation + pré-sélection UI).
- request-AC6 -> This backlog slice. Proof: AC6 (reprise après redémarrage testée).
- request-AC7 -> This backlog slice. Proof: AC7 (états corrompus sans crash).
- request-AC8 -> This backlog slice. Proof: AC8 (cap LRU + purge testés).
- request-AC9 -> This backlog slice. Proof: AC9 (workspace hors dépôt, env var).
- request-AC10 -> This backlog slice. Proof: AC10 (mode éphémère inchangé).
- request-AC11 -> This backlog slice. Proof: AC11 (ruff, pytest, E2E, README).

# Decision framing
- Product framing: Not needed
- Product signals: (none detected)
- Product follow-up: No product brief follow-up is expected based on current signals.
- Architecture framing: Recommended
- Architecture signals: introduction d'un stockage persistant utilisateur qui
  remplace les tempdirs et modifie le cycle de vie de la session serveur
- Architecture follow-up: consigner la disposition du workspace (emplacement XDG,
  manifest versionné, politique LRU/purge, mode éphémère) dans un ADR court lors
  de l'implémentation, en cohérence avec `docs/adr/0004-donnees-locales-hors-depot.md`.

# Links
- Product brief(s): (none yet)
- Architecture decision(s): `docs/adr/0004-donnees-locales-hors-depot.md`
- Request: `logics/request/req_006_workspace_local_lancement_1_clic_bibliotheque_dbc_et_reprise_de_session.md`
- Primary task(s): (none yet)

# AI Context
- Summary: Livrer le workspace local persistant : lanceur Windows 1-clic +
  `serve --open`/auto-port/probe d'instance, bibliothèque DBC dédupliquée par
  hash avec LRU et purge, et reprise de la dernière analyse (DuckDB + manifest)
  au redémarrage, avec mode éphémère préservé.
- Keywords: backlog-groom, workspace, launcher, wsl, one-click, dbc-library,
  session-restore, duckdb-persistence, lru, serve-open
- Use when: Use when implementing or reviewing the local workspace delivery
  slice (launcher, DBC library, session persistence, workspace storage).
- Skip when: Skip when the change targets decoding accuracy, trace formats,
  export, timing analysis, or UI features unrelated to import/session lifecycle.

# Implementation notes
- Préserver la sémantique transactionnelle de session durcie par req_003 : le
  store précédent reste intact jusqu'au succès du nouveau, y compris avec le
  workspace persistant (écrire le nouveau DuckDB à côté, basculer à la fin).
- Versionner le schéma dans le manifest et invalider proprement (état vide +
  message) plutôt que tenter d'ouvrir un DuckDB incompatible.
- Centraliser la résolution du répertoire workspace dans un module unique
  consommé par l'API, le CLI et les fixtures de tests (env var de surcharge).
- L'ouverture navigateur depuis WSL (`explorer.exe`/`wslview`) doit être
  best-effort : un échec loggé ne bloque jamais le démarrage du serveur.
- Le script PowerShell génère le raccourci avec le chemin réel du dépôt du poste
  (pas de chemin codé en dur dans le `.cmd`).
- Couvrir l'éviction LRU des fichiers orphelins (DBC référencés par aucun
  manifest) pour éviter la fuite d'espace disque.

# Priority
- Priority: High
- Rationale: Friction subie à chaque session de travail sur les deux postes de
  l'opérateur ; le gain quotidien (1 clic, zéro ré-import) dépasse celui des
  fonctions d'analyse additionnelles encore en attente.

# Notes
- Hybrid rationale: Derived from request `req_006_workspace_local_lancement_1_clic_bibliotheque_dbc_et_reprise_de_session` and kept bounded to one coherent delivery slice.
- Source file: `logics/request/req_006_workspace_local_lancement_1_clic_bibliotheque_dbc_et_reprise_de_session.md`.
- Generated locally by logics-manager.

# Tasks
- `task_016_workspace_local_lancement_1_clic_bibliotheque_dbc_et_reprise_de_session`
