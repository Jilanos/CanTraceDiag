# Audit code & projet — CanTraceDiag — 2026-07-23

Audit réalisé sur `main` (`7c139c7`), working tree propre, avant commit/push.

## 1. Méthodologie & outillage

| Vérification | Résultat |
| --- | --- |
| `ruff check .` | ✅ All checks passed |
| `pytest` (unitaires + intégration) | ✅ **126 passés** |
| `pytest` (e2e Playwright) | ⚠️ 21 erreurs — binaire Chromium absent en local (environnement, pas le code ; le CI l'installe) |
| Hygiène dépôt | ✅ `.gitignore` complet, aucun artefact généré versionné (`__pycache__`, `egg-info`, caches) |
| Cohérence README ↔ arborescence | ✅ `web/js/` et `docs/adr/0007` présents |

Périmètre : `src/cantracediag/` (~2 700 lignes Python), frontend `web/js/` (~1 700 lignes JS),
suite de tests (~2 400 lignes), CI, documentation.

## 2. Synthèse

Le projet est **globalement sain et bien tenu** : lint propre, suite de tests fournie et verte,
paramétrage SQL rigoureux, modèle de sécurité local-first cohérent (token constant-time,
défense DNS-rebinding, désactivation de l'import serveur en LAN). Les points ci-dessous sont
des améliorations, aucun n'est bloquant pour un usage local mono-utilisateur — cible réelle du produit.

**À traiter en priorité :** (H1) verrou DuckDB tenu pendant tout le streaming d'export, et
(S1) fuite possible de chemins locaux dans les messages d'erreur DBC/import.

## 3. Correctness

### H1 — Verrou DuckDB tenu pendant tout le streaming d'export — **Haute**
`store.py:482-484` — `iter_export_batches` fait `with self._lock: ... yield from reader`.
Ce générateur est consommé paresseusement par `StreamingResponse` (`api.py:925/927/929-935`)
pour les formats CSV et `csv_wide`. Le `RLock` partagé de la connexion reste donc tenu pendant
toute l'écriture de la réponse HTTP : un téléchargement lent ou bloqué gèle toutes les autres
requêtes DuckDB du store (`/api/series`, `/api/cursor`, `/api/trace`), ce qui annule les
garanties de concurrence que le cycle de vie référencé du store (AC3) est censé offrir.
Le format Parquet n'est pas concerné (drainé sous verrou vers un fichier temporaire avant envoi).
*Piste :* matérialiser sous verrou puis streamer hors verrou, ou emprunter une connexion dédiée
au stream.

### M1 — Floats interpolés dans le SQL de décimation — **Moyenne**
`store.py:653-656` — `_decimate` insère `t_lo`/`span` via `!r` au lieu de paramètres liés.
Ce ne sont pas des chaînes utilisateur (pas d'injection classique), mais un `inf`/`nan` issu
d'un timestamp pathologique produirait du SQL dégénéré. À lier comme partout ailleurs.

### M2 — Filtre signal sans correspondance catalogue : fallback silencieux — **Moyenne**
`api.py:440-449` / `store.py:949-960` — `_signal_ids_matching` renvoie `[]` (et non `None`)
quand le terme ne matche aucun signal. `signal_ids=[]` étant falsy, `_trace_union` n'exclut rien
et `_frame_filters` bascule sur la sous-requête `EXISTS` contre `samples` (vide tant qu'aucun
signal n'a été tracé, décodage paresseux `pipeline.py:43/118`). Le comportement dépend donc de
ce qui a été décodé. Devrait court-circuiter vers « aucune ligne ».

### L1 — `series_cache` jamais purgé sur `replace_signal_samples` — **Basse**
`store.py:229-247` & `56-63` — les fenêtres qui se recouvrent ajoutent des lignes sans supprimer
les anciennes ; `cache_stats` sur-compte les doublons. Impact métriques seulement, mais la table
croît sans borne.

### L2 — `frame_at` / `frame_signals` : égalité flottante exacte — **Basse**
`store.py:516-541` / `1016-1027` — `WHERE timestamp_s = ?` suppose que le client renvoie le double
exact reçu. Tout arrondi JS produit un inspecteur silencieusement vide plutôt qu'une erreur.

### L3 — ASC : arête `dlc==0` + métadonnées numériques parasites — **Basse**
`formats/asc.py:249-252` — le parseur consomme gloutonnement les tokens numériques de tête comme
octets de payload. Un DLC 0 suivi de métadonnées numériques (rare mais légal dans certains
dialectes ASC) serait déclassé en anomalie « payload plus long que DLC ». À couvrir par une fixture.

## 4. Sécurité

Modèle local-first solide dans l'ensemble : paramétrage SQL exhaustif (toutes les chaînes
utilisateur liées, `LIMIT` coercé via `int()`), `_safe_name` réduit au basename (anti-traversal
upload), `library_path` ne résout que des clés-digest connues, `token_ok` en temps constant.
Les points ci-dessous sont de la défense en profondeur.

### S1 — Chemins locaux possiblement exposés dans les erreurs DBC/import — **Moyenne**
`api.py:273-275, 335, 383, 409` — `f"Invalid DBC: {exc}"` et `session.job("failed", ..., str(exc))`
propagent des messages `cantools`/OS bruts, qui incluent couramment le chemin fautif (chemin temp
d'upload, ou chemin serveur **réel** pour `/api/import`). Ce détail est ensuite renvoyé tel quel
par `/api/import-job` et affiché dans l'UI — ce qui viole l'intention d'AC10. Seul le cas
fichier-manquant est nettoyé et testé (`test_security.py:138`) ; les cas parse-error et
import-failure ne le sont pas.

### S2 — Token accepté en query string + URL LAN `?token=` — **Moyenne**
`api.py:240` & `cli.py:181/193` — le garde lit `request.query_params.get("token")` et `serve()`
imprime/ouvre `http://host:port/?token=<token>`. Avec `uvicorn ... log_level="info"`, le token
atterrit dans les logs d'accès, l'historique navigateur et d'éventuels logs proxy. Préférer
l'en-tête seul, ou au minimum éviter `log_level="info"` quand un token de query est en jeu.

### S3 — Plafond d'upload par fichier seulement, pas d'agrégat — **Moyenne**
`api.py:531-533` & `1052-1066` — le pré-contrôle `Content-Length` et `_spool` appliquent
`max_upload_bytes` par fichier. Une requête (1 trace + N DBC) peut écrire `N × max_upload_bytes`
dans le temp dir ; le plafond disque effectif n'est pas borné. Ajouter un cumul par requête.

### S4 — `/api/import` = lecture de fichier local arbitraire (par conception) — **Moyenne (à documenter)**
`api.py:488-503` — `normalize_local_path` résout n'importe quel chemin collé (`..`, `/etc/...`,
`/mnt/c/...`) sans confinement à une racine. Intentionnellement loopback-only / désactivé en LAN
(AC11), mais sans allowlist de racine : sur loopback, l'UI peut lire tout fichier accessible au
process. À expliciter dans le threat model.

### S5 — En-têtes `Host`/`Origin` absents traités comme autorisés — **Basse**
`security.py:115, 118-119` — `host_allowed` renvoie `True` si `Host` absent, `origin_allowed`
`True` si `Origin` absent. Un client non-navigateur peut les omettre pour contourner les gardes
rebinding/cross-site (et en mode local les GET ne requièrent alors pas de token). Le binding
loopback limite l'exposition réelle, mais le défaut « absent = autorisé » mérite d'être resserré.

## 5. Qualité & maintenabilité

- **M3 — `create_app` ~770 lignes de closures imbriquées** (`api.py:218-988`). `_preview_unresolved`
  (299-354) et `_finalize` (356-420) dupliquent quasi toute la séquence build/erreur/assignation
  de session ; risque de dérive entre les deux chemins d'import. Difficile à tester unitairement.
- **L4 — `_f` défini deux fois à l'identique** (`store.py:1030-1032` et `1081-1083`) — doublon mort.
- **L5 — `iter_asc` sans appelant** (`formats/asc.py:97-107`) — code mort ; seuls `parse_asc`
  (tests) et `stream_asc` (pipeline) sont référencés.
- **L6 — `api_export` réimplémente le cycle acquire/release du store** (`api.py:856-935`) en
  accédant à `session._lock` privé, car le context manager `use_store()` ne couvre pas une réponse
  streamée. Un helper « borrow for streaming » supprimerait cet accès privé et les 3 sites de
  `release()`.

## 6. Couverture de tests — lacunes

- **Concurrence pendant export streaming** (fort intérêt) — aucun test n'assure qu'une requête
  concurrente progresse pendant un export ; attraperait H1.
- **Fuite de chemins** sur erreurs parse-DBC / import-serveur — seul `test_missing_file_error_...`
  existe ; `api.py:275` et le détail d'échec d'`import-job` (335/383) sont non testés (et fuient).
- **Taille d'upload agrégée** — seul le cas mono-fichier est couvert (S3).
- **Filtre signal sans correspondance catalogue** (M2) — non testé.
- **Token via query param** (`api.py:240`, S2) — non testé.
- **`_decimate` entrées dégénérées** (`nan`/`inf`/point unique, M1) — non testé.
- **`normalize_local_path` avec `..`** — `test_paths.py` couvre WSL/drive/POSIX mais jamais un
  chemin `..` (surface de lecture arbitraire non documentée par les tests).

## 7. Recommandations priorisées

1. **H1** — sortir la consommation du reader du verrou pour les exports CSV/wide.
2. **S1** — nettoyer les messages d'erreur DBC/import (comme le cas fichier-manquant) + tests.
3. **S3** — plafond d'upload agrégé par requête + test.
4. **M1/M2** — paramétrer `_decimate` ; court-circuiter le filtre signal vide.
5. **S2** — token en en-tête only / baisser `log_level` ; **S4/S5** — documenter dans le threat model.
6. **Nettoyages** — L4 (doublon `_f`), L5 (`iter_asc` mort), M3 (extraire `_preview_unresolved`/`_finalize`).

## 8. Points positifs

- Lint propre, 126 tests verts, fixtures synthétiques anonymisées.
- Paramétrage SQL rigoureux, `_safe_name`/`library_path` anti-traversal, token constant-time.
- `.gitignore` protège traces/DBC/caches réels ; ADR à jour (jusqu'à 0007).
- Décodage paresseux + fenêtrage DuckDB : UI réactive à mesure que les traces grossissent.
