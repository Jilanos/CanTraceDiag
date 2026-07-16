# ADR 0006 - Workspace local persistant (bibliothèque DBC + reprise de session)

## Statut

Accepté

## Contexte

La session API était intégralement éphémère : DuckDB d'analyse et DBC uploadés
vivaient dans des `tempfile.mkdtemp` détruits au redémarrage du serveur. Sur un
poste Windows+WSL, l'opérateur re-sélectionnait et re-téléversait trace et DBC à
chaque session, alors que les DBC changent rarement et que l'index DuckDB peut
être réouvert sans re-parser l'ASC. Voir req_006 / item_016.

## Décision

- Introduire un répertoire de données utilisateur, résolu par
  `CANTRACEDIAG_DATA_DIR`, sinon `$XDG_DATA_HOME/cantracediag`, sinon
  `~/.local/share/cantracediag/`, conformément à l'ADR 0004 (hors dépôt).
- Disposition : `dbc/` (bibliothèque indexée par hash de contenu,
  `dbc/<digest>/<nom_original>` + `dbc/index.json`), `analysis/<uuid>/analysis.duckdb`
  (seule la dernière analyse est conservée), `last-analysis.json` (manifest).
- Le nom de fichier d'origine du DBC est préservé dans la bibliothèque : le
  décodage et la résolution de conflits reposent sur ce basename, la reprise
  doit donc recharger les DBC sous leur nom d'origine.
- Persistance transactionnelle : chaque analyse est écrite dans un dossier
  `analysis/<uuid>/` neuf ; le manifest ne bascule sur ce dossier qu'au succès
  de l'import, préservant la sémantique durcie par req_003 (le store précédent
  reste intact jusqu'au succès du nouveau).
- Manifest versionné (`SCHEMA_VERSION`) : un manifest de version différente,
  absent ou incohérent (DuckDB ou DBC manquant) est ignoré et le serveur
  démarre sur un état vide, sans planter.
- Bibliothèque bornée par un cap LRU configurable (`CANTRACEDIAG_DBC_CAP`,
  défaut 20) ; une purge supprime bibliothèque et dernière analyse.
- Mode éphémère conservé (`CANTRACEDIAG_EPHEMERAL=1` ou `Workspace(ephemeral=True)`)
  reproduisant le comportement tempdir d'avant ; c'est le mode par défaut de la
  suite de tests, qui n'écrit donc jamais dans le profil réel.

## Conséquences

- `api.py` route la création/ouverture des stores et l'alimentation de la
  bibliothèque via le module `workspace.py` ; `serve` démarre en mode persistant,
  les tests en mode éphémère.
- Au démarrage en mode persistant, l'app tente de restaurer la dernière analyse
  (réouverture du DuckDB + rechargement des DBC de bibliothèque) et l'expose via
  `/api/status` ; le frontend restaure ensuite sélection/filtres depuis
  localStorage sans ré-import.
- Une évolution du schéma DuckDB ou de la disposition impose de bumper
  `SCHEMA_VERSION` pour invalider proprement les anciennes analyses.
- Le cap LRU et le prune des orphelins bornent l'espace disque consommé.
