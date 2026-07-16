# Audit complet CanTraceDiag — 16 juillet 2026

Date : 16 juillet 2026
Périmètre : performance, fonctionnalités, UI, design, accessibilité, robustesse,
sécurité locale, tests et dette technique.
Version auditée : `8428922` (`main`).
Audit précédent : `docs/audit-bout-en-bout-2026-07-15.md` (version `d71bbad`).

## 1. Synthèse exécutive

Le lot P0 issu de l'audit du 15 juillet est **réellement corrigé et testé** : les
conflits DBC de même nom sont détectés par empreinte canonique, la résolution est
validée serveur avec pop-up opérateur, l'injection HTML est neutralisée (échappement
systématique + CSP + test hostile E2E), et la CI installe désormais les extras
nécessaires. La suite passe de 50 à 63 tests, tous verts. La confiance diagnostic de
base est rétablie.

En revanche, `req_002` est marquée `Done` alors que **les slices 2 à 5 sont au mieux
entamées**. Les points ouverts majeurs sont :

1. **L'import uploadé bloque l'event loop asyncio** : pendant le décodage d'une grosse
   trace, toute l'API est gelée, y compris le polling de progression.
2. **La progression et l'annulation d'import sont factices** : les endpoints existent
   mais l'UI ne les interroge jamais, et « cancel » ne fait que changer un libellé.
3. **L'état de session est partagé sans verrou** : un import concurrent d'une requête
   `/api/series` peut fermer/supprimer le store DuckDB en cours d'utilisation.
4. **Des endpoints chauds sont en O(N)** : `/api/cursor` (full scan à chaque survol),
   pagination `OFFSET` + `count(*)` recalculé, `/api/series` sans index sur
   `(message_name, signal_name)`.
5. **Une erreur silencieuse au chargement peut bloquer toute l'UI** : un seul
   `/api/series` en échec pendant `restoreSelected` interrompt l'initialisation sans
   message.
6. **L'export CSV/Parquet est absent** — le manque fonctionnel le plus critique pour
   un workflow de diagnostic (promis au backlog P1 et roadmap Phase 4).

Évaluation synthétique (l'évolution est mesurée par rapport au 15 juillet) :

| Axe | État | Note | Évolution |
|---|---|---|---|
| Justesse diagnostic | Conflits DBC maîtrisés, testés | 8/10 | +4 |
| Sécurité UI (XSS) | Échappement + CSP + test hostile | 8/10 | nouveau |
| Sécurité réseau locale | DNS rebinding, lecture fichiers arbitraires | 4/10 | nouveau |
| Fonctionnel | P0 complet, export absent, job d'import cosmétique | 7/10 | = |
| UI desktop | Dense, lisible, erreurs réseau avalées | 6/10 | -1 |
| Responsive | 390 px traité, 1280/1024 non corrigés | 4/10 | +2 |
| Accessibilité | Canvas clavier ✔, favoris/tables souris only | 5/10 | +1 |
| Performance interactive | Bonne, mais curseur O(N) et rafales réseau | 6/10 | -2 |
| Scalabilité import | Disque ✔, event loop bloqué, batch non borné | 5/10 | = |
| Qualité automatisée | 63 tests + CI réparée, zéro test CLI/perf/JS | 7/10 | = |

Verdict : **outil de diagnostic desktop fiable sur le plan de la justesse, mais pas
encore robuste ni scalable — la priorité bascule de la correction vers la robustesse
d'exécution (concurrence, jobs d'import) et la complétude produit (export, erreurs UI).**

## 2. Méthode

- Lecture intégrale du code backend (`store.py`, `api.py`, `pipeline.py`, `decode.py`,
  `dbc.py`, `formats/asc.py`, `models.py`, `cli.py`) et frontend (`app.js`,
  `index.html`), en trois passes parallèles indépendantes (backend/performance,
  frontend/UI/design, couverture fonctionnelle vs backlog/roadmap/audit précédent).
- Exécution de la suite de tests : **63 passed** (~9,4 s), 1 warning de dépréciation
  (`starlette.testclient` / `httpx`).
- Croisement avec `docs/audit-bout-en-bout-2026-07-15.md`, `req_002`, le backlog, la
  roadmap et le git log (`461a04d`, `8428922`).
- Pas de nouvelle mesure sur traces réelles dans cet audit ; les mesures du 15 juillet
  (8,2 s/396 Mo pour 44 Mo sans DBC ; 24,4 s/850 Mo pic avec 14 DBC) restent la
  référence, l'architecture d'ingestion n'ayant pas changé sur ces chemins.

## 3. Performance

### 3.1 Backend — bloquants pour les traces volumineuses

| Réf | Sévérité | Constat | Localisation |
|---|---|---|---|
| P-01 | Critique | `api_import_files` est `async def` mais exécute parse + décodage + insertion de façon synchrone dans l'event loop : toute l'API est gelée pendant l'import (y compris `/api/import-job`). | `api.py:252-297` |
| P-02 | Majeur | Le flush par lots teste `frame_batch` et `event_batch` mais jamais `sample_batch` : un message à 30-60 signaux accumule jusqu'à ~3 M de dicts en RAM avant flush. | `pipeline.py:87` |
| P-03 | Majeur | `nearest_sample` fait `ORDER BY abs(timestamp_s - ?)` : full scan + tri à chaque survol de curseur. | `store.py:292-312` |
| P-04 | Majeur | Pagination `OFFSET` + `count(*)` recalculé à chaque page ; `locate_row` matérialise un `row_number()` sur toute l'union. | `store.py:342-399` |
| P-05 | Majeur | Annulation d'import factice : `api_import_cancel` change un libellé, rien ne vérifie de drapeau d'annulation dans le pipeline ; la progression saute de 0.35 à 1.0. | `api.py:436-441` |
| P-06 | Mineur | Aucun index sur `(message_name, signal_name)` de `samples` : chaque `/api/series` scanne toute la table. | `store.py:20-53`, `209-236` |
| P-07 | Mineur | Ingestion via listes de dicts → `pd.DataFrame` par inférence : chemin lent ; `pyarrow` est en dépendance mais jamais utilisé. | `store.py:145-153` |
| P-08 | Mineur | Décodage cantools trame par trame ; `units` reconstruit à chaque trame au lieu d'un cache par message. | `decode.py:65-96` |

### 3.2 Frontend

| Réf | Sévérité | Constat | Localisation |
|---|---|---|---|
| P-10 | Majeur | Le token anti-course des séries ne protège que le rendu, pas l'état : une réponse périmée écrase `entry.t/v` et le rendu suivant affiche des données obsolètes. | `app.js:312-326` |
| P-11 | Majeur | Le readout curseur émet N signaux × 2 curseurs requêtes `/api/cursor` toutes les 90 ms pendant un drag (16 req/tick à 8 signaux), sans protection d'ordre. | `app.js:629-649` |
| P-12 | Mineur | `getComputedStyle` appelé des dizaines de fois par frame de rendu ; `renderPlot` non coalescé en rAF ; handler `window.mousemove` global recalculant la géométrie au repos. | `app.js:8`, `376-467`, `562-585` |
| P-13 | Mineur | Échelle Y recalculée sur la fenêtre visible : l'axe « saute » à chaque pan/zoom ; `minimum`/`maximum` DBC déjà exposés par l'API mais inutilisés. | `app.js:387-391` |

## 4. Robustesse et concurrence

| Réf | Sévérité | Constat | Localisation |
|---|---|---|---|
| R-01 | Critique | État de session global sans verrou : `replace_store` ferme et supprime le store DuckDB pendant que des requêtes concurrentes l'utilisent ; courses aussi sur `session.pending`. Le `RLock` du store protège la connexion, pas son cycle de vie. | `api.py:83-94`, `117`, `302-320` |
| R-02 | Majeur | Tri de pagination sur `timestamp_s` seul (non déterministe en rafales CAN) : doublons/trous entre pages, `locate_row` incohérent avec la page servie. La colonne `seq` existe mais n'est jamais utilisée. | `store.py:349`, `393` |
| R-03 | Majeur | Jointure trame↔signaux par égalité flottante `(timestamp_s, arbitration_id)` sans canal : mélange possible entre canaux, fragilité du round-trip float JSON→SQL. | `store.py:489-500`, `552-563` |
| R-04 | Majeur | Lignes ASC tronquées acceptées sans signalement (`tokens[5:5+dlc]` non vérifié) ; tokens d'attributs de fin de ligne font rétrograder la trame entière en événement `Other` ; DLC ≤ 64 accepté alors que CAN classique ≤ 8. | `formats/asc.py:207-213` |
| R-05 | Majeur | La session précédente est détruite dès le début du nouvel import (`clear_store` avant décodage), contrairement à la décision produit AC8 de req_002. | `api.py` (`_preview_unresolved`) |
| R-06 | Mineur | Id de job réutilisé entre imports ; phase `cancelled` déclarée `cancellable: True` ; clés de résolution invalides avalées silencieusement. | `api.py:96-103`, `511-519` |
| R-07 | Mineur | Timestamps négatifs (triggerblock) ou en notation scientifique invisibles (ni frame ni event), contredisant la promesse « rien n'est perdu ». | `formats/asc.py:19`, `58-60` |
| R-08 | Mineur | `normalize_local_path` casse les vrais chemins UNC et accepte les chemins relatifs. | `api.py:453-476` |

## 5. Sécurité locale

| Réf | Sévérité | Constat | Localisation |
|---|---|---|---|
| S-01 | Majeur | `/api/import` = lecture de fichiers arbitraires du serveur sans auth ni vérification `Host`/`Origin` : vulnérable au DNS rebinding ; toute page atteignant `127.0.0.1:8000` peut faire parser un fichier et lire son contenu via `/api/trace`. `serve --host 0.0.0.0` expose au LAN. | `api.py:237-250`, `cli.py:52` |
| S-02 | Mineur | Uploads sans plafond de taille (remplissage disque) ; POST multipart sans preflight → écrasement de session possible par une page tierce. | `api.py:252-300` |
| S-03 | Mineur | Messages d'erreur renvoyant chemins et détails internes (oracle d'existence de fichiers). | `api.py:141-143` |
| S-04 | — | Points sains vérifiés : pas de path traversal sur uploads (`_safe_name`), SQL paramétré, XSS corrigé et testé. | `api.py:487-489` |

## 6. Fonctionnalités

### 6.1 Implémenté et vérifié
- Import `.asc` en flux (hex + décimal, IDs standard/étendus, événements conservés).
- Multi-DBC avec détection exhaustive d'ambiguïtés par empreinte canonique
  (multiplexage inclus), résolution opérateur validée, import en deux phases.
- Décodage cantools complet avec statuts (`ok`, `unknown_id`, `no_database`,
  `decode_error`, `ambiguous_id`) et `dbc_source` audité par trame.
- Graphes empilés à axe temporel partagé, downsampling min/max serveur, zoom/pan,
  curseurs A/B avec deltas, sync graphe↔trace bidirectionnelle.
- Vue trace paginée avec filtres serveur combinables (temps, ID, message, signal,
  direction, statut, événement), formats de colonnes (temps s/ms/hms, hex/dec/bin),
  recherche signaux (message/signal/ID/unité/DBC) avec facette présent/absent.

### 6.2 Partiel
- **Job d'import** : endpoints présents, mais UI muette (« Indexing… » statique),
  annulation factice, progression sans phases intermédiaires (voir P-01, P-05).
- **Vue trace** : pas de redimensionnement de colonnes à la souris, pas de filtre par
  canal, pas de saut « aller à t= », navigation limitée à Prev/Next par 200 lignes.
- **README** : annonce une table « virtualisée » (c'est une pagination) et 54 tests
  (il y en a 63).
- **Traces volumineuses** : DuckDB sur disque ✔ (voie API), mais aucun budget
  temps/mémoire documenté ni protégé en CI (AC7 de req_002 non tenu).

### 6.3 Manquant
- **Export CSV/Parquet** (backlog P1, roadmap Phase 4) : aucun code. Manque le plus
  critique pour un ingénieur diagnostic.
- **Cache/persistance serveur** : tout import est perdu au redémarrage ; pas de
  « rouvrir la dernière analyse ».
- **Statistiques entre curseurs** (min/max/moyenne sur [A,B]) : seulement les deltas.
- **Bookmarks/annotations temporelles** ; **recherche de motif hex dans le payload** ;
  **navigation occurrence suivante d'un ID** ; **superposition de signaux sur un axe**.
- **Rapport d'import global** listant la DBC retenue par ID (visible seulement par
  trame dans l'inspecteur).
- **Abstraction de format** pour BLF/MF4 : `formats/` n'a que `asc.py`, le concept
  `asc_base` fuit jusqu'à l'API ; `python-can` déclaré mais inutilisé.

## 7. UI / UX

| Réf | Sévérité | Constat | Localisation |
|---|---|---|---|
| U-01 | Critique | Un seul `/api/series` en échec pendant `restoreSelected` (Promise.all sans catch) interrompt tout `onLoaded` : plot non rendu, table vide, aucun message. | `app.js:296-326` |
| U-02 | Majeur | Le dialog de conflit DBC se ferme avec Échap sans issue de secours : session serveur en `Pending`, aucun moyen de rouvrir la pop-up. | `app.js:170-203`, `index.html:258-265` |
| U-03 | Majeur | Aucune progression ni annulation pendant l'indexation côté UI (endpoints jamais appelés). | `app.js:122` |
| U-04 | Majeur | `loadTrace` et `toggleSignal` sans gestion d'erreur : rejets non gérés, table figée, checkbox incohérente, bande vide sans explication. | `app.js:278-294`, `718-731`, `997-1009` |
| U-05 | Majeur | Pattern `catch (_) {}` systématique (readout, locate, inspecteur, init) : les erreurs réseau ET les bugs sont avalés en silence. | `app.js:645`, `691`, `822`, `1063` |
| U-06 | Mineur | Shift+clic (curseur B) et raccourcis flèches non documentés dans l'UI ; pas d'état vide « aucune ligne ne correspond aux filtres » ; filtres temporels non persistés ; sélection de ligne par égalité flottante de timestamp. | `app.js:603-617`, `710-716`, `733-750`, `index.html:204` |

## 8. Design et accessibilité

| Réf | Sévérité | Constat | Localisation |
|---|---|---|---|
| D-01 | Majeur | Thème sombre uniquement, aucun `prefers-color-scheme` ; palette en dur dans `:root` (le code lit déjà tout via variables CSS, coût de correction faible). | `index.html:9-15` |
| D-02 | Majeur | Étoile « favori » = `span` cliquable : ni focusable, ni rôle, ni état annoncé. | `app.js:259-269` |
| D-03 | Majeur | Interactions du graphe 100 % souris (`mousedown/wheel/dblclick`) : inutilisable au tactile ; pas de Pointer Events. | `app.js:546-617` |
| D-04 | Mineur | Filtres identifiés uniquement par placeholder (pas d'`aria-label`) ; lignes de table non focusables ; boutons glyphe seul (`‹`/`›`) à cible ~16 px ; styles inline dans les dialogs. | `index.html:216-223`, `app.js:739-749`, `904-905` |
| D-05 | — | Points sains : `:focus-visible` stylé, canvas `role="img"` + `aria-label` + clavier, contrastes vérifiés conformes, breakpoint 700 px testé en E2E. | `index.html:38-40`, `207` |
| D-06 | Majeur | Responsive 1280×720 et 1024×768 non corrigés (débordement ~1447 px constaté le 15 juillet, aucun correctif dédié ni test) ; AC13 de req_002 non tenu. | `index.html:139-153` |

## 9. Qualité de code et dette

- **Frontend monolithique** : `app.js` = 1064 lignes en portée globale, sans module ni
  lint JS. Attention : les tests E2E accèdent à `state`/`toggleSignal`/`setView` via
  `page.evaluate` — un découpage en modules ES doit préserver une surface de test
  explicite (`window.__ctd`).
- **Code mort** : `iter_asc` (aucun appelant), `_window_clause` (`store.py:565-575`),
  champs `raw_value`/`quality` de `DecodedSignalSample` jamais renseignés, caches de
  rendu `s._yOf/_top/_bot` jamais relus.
- **Dépendances** : `pyarrow` et `python-can` déclarés mais jamais importés ;
  `fastapi` en extra optionnel alors que `api.py` s'importe sans garde.
- **Duplication** : `_id_hex` défini dans `api.py:506` et `store.py:578`.
- **`api()` frontend** suppose `detail` textuel : une 422 FastAPI affiche
  `[object Object]`.

## 10. Tests

Couvert (63 tests verts) : parsing ASC, ambiguïtés DBC (y compris même nom et
multiplexage), statuts de décodage, store (séries, nearest, pagination, filtres,
downsampling), flux API complet avec résolution de conflit, E2E Playwright (curseurs,
pan, clavier, collapse, rafales concurrentes, XSS hostile, viewport 390 px).

Non couvert :
- Budget performance/mémoire (aucune trace synthétique volumineuse en CI — AC7).
- Responsive 1280×720 / 1024×768.
- Progression, annulation et préservation de session du job d'import.
- Persistance des formats/largeurs de colonnes et restauration des filtres.
- `cli.py` : zéro test.
- Chemins d'erreur UI (échec `/api/series`, trace vide) ; pas d'axe-core ni lint JS.
- Les E2E s'auto-skippent si Chromium est indisponible : la CI peut passer sans
  exécuter un seul test navigateur.

## 11. Recommandations priorisées

- **P0 — Robustesse d'exécution** (bloquant pour l'usage réel) :
  import hors event loop avec vraie progression et annulation effective (P-01, P-05,
  U-03), verrouillage du cycle de vie de session (R-01), préservation de la session
  précédente jusqu'au succès (R-05), gestion d'erreurs UI unifiée (U-01, U-04, U-05),
  issue de secours du dialog de conflit (U-02).
- **P1 — Performance des endpoints chauds** : curseur borné (P-03), pagination keyset
  + tri stable sur `seq` (P-04, R-02), index/clé signal (P-06), flush `sample_batch`
  (P-02), endpoint curseur batch + interpolation locale pendant le drag (P-11), commit
  atomique des séries (P-10).
- **P1 — Complétude produit** : export CSV/Parquet de la sélection et de la plage
  [A,B], statistiques entre curseurs, rapport d'import global des résolutions DBC,
  saut « aller à t= ».
- **P1 — Sécurité locale** : `TrustedHostMiddleware` + token de session type Jupyter,
  plafond de taille d'upload, vérification `Origin` (S-01, S-02).
- **P2 — UI/design** : thème clair (D-01), accessibilité favoris/table/filtres (D-02,
  D-04), responsive 1280/1024 (D-06), Pointer Events (D-03), robustesse parsing ASC
  (R-04, R-07).
- **P2 — Dette** : découpage `app.js` en modules ES avec surface de test préservée,
  suppression du code mort, hygiène des dépendances, tests CLI, budget perf synthétique
  en CI, E2E non skippables silencieusement en CI.

## 12. Références

- `docs/audit-bout-en-bout-2026-07-15.md`
- `logics/request/req_002_fiabiliser_cantracediag_apres_audit_fonctionnel_ui_et_performance.md`
- `docs/product-backlog.md`, `docs/roadmap.md`
- `src/cantracediag/` (backend + `web/`), `tests/`, `.github/workflows/ci.yml`
