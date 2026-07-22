# Audit — Refonte « full frontend » (PWA local-first) — 22 juillet 2026

Date : 22 juillet 2026
Périmètre : revue de la refonte de CanTraceDiag en version *full frontend* statique
destinée à être hébergée sur un site de projet (`cantracediag.paulmondou.fr`).
Couvre : le PWA statique déployable (`spikes/pwa-local-engine/`), la parité du
moteur ASC/DBC porté en TypeScript vis-à-vis de l'oracle Python, et les nouvelles
features diagnostic ajoutées au produit FastAPI.
Version auditée : working tree de la branche `feat/pwa-local-first` (aucun commit).
Audit précédent : `docs/audit-complet-2026-07-16.md` (version `8428922`).

## 1. Synthèse exécutive

**Verdict : pas prêt à héberger.** L'architecture est saine (backend embarqué en
mémoire, CSP stricte, build reproductible, `.mjs` compilés fidèles aux `.ts`), mais
plusieurs bloquants doivent être levés avant tout déploiement public.

Point préalable : **il n'y a aucun commit** sur `feat/pwa-local-first` — la branche
est à 0 commit d'avance sur `main`. Toute la refonte est en *working tree* non
commité, et l'artefact déployable (`spikes/pwa-local-engine/site/`) est un dossier
de *spike* non suivi par git. Il n'existe donc aucune provenance versionnée de ce
qui serait déployé.

La refonte se répartit sur deux pistes parallèles :
- **PWA statique déployable** — `spikes/pwa-local-engine/` : moteur ASC/DBC porté
  en TS, `site/` généré, service worker, workspaces navigateur.
- **Nouvelles features diagnostic** ajoutées au **produit FastAPI** (qui reste
  l'oracle de correction) : stats de plage, rapport, export CSV/Parquet,
  `security.py`, découpage du front en `web/js/*.js`.

Bloquants majeurs :

1. **Le service worker rend le site non-actualisable après la 1ʳᵉ visite.**
2. **Le moteur navigateur ne décode pas des traces réelles courantes** : IDs
   étendus 29 bits, signaux Motorola/big-endian, et multiplexage.
3. **Le produit FastAPI a deux régressions bloquantes** : `/api/trace` renvoie 500
   au chargement, et le middleware sécurité met la suite de tests à 28 échecs.
4. **Du code mort contradictoire** subsiste (`app.js` modifié mais non chargé).

| Axe | État | Note |
|---|---|---|
| Déployabilité PWA (SW, manifest, hosting) | Bloqué par le cycle de vie SW | 4/10 |
| Parité moteur navigateur vs Python | Gaps majeurs (29 bits, Motorola, mux) | 4/10 |
| Régressions produit FastAPI | 2 bloquants, tests rouges | 3/10 |
| Sécurité / posture hosting statique | Saine (CSP, pas de secret ni fetch) | 8/10 |
| Reproductibilité build | Déterministe, sans dépendance | 8/10 |
| Versionnement / provenance | Rien de commité | 2/10 |

## 2. Bloquants pour l'hébergement — PWA statique

### 2.1 — 🔴 Service worker non-actualisable après la 1ʳᵉ visite
`spikes/pwa-local-engine/site/sw.js:1,19-22`

`CACHE_NAME` est figé à `-v1` et le build (`build-browser.mjs:31`) recopie `sw.js`
à l'identique à chaque déploiement. Un navigateur ne réinstalle un SW que si les
*octets* de `sw.js` changent → ils ne changent jamais → `install`/`addAll` ne se
rejoue jamais et `activate` ne purge jamais l'ancien cache. Avec un fetch handler
**cache-first** (`sw.js:36`) qui intercepte aussi les navigations, `index.html` et
les `*.mjs` sont servis indéfiniment.

*Scénario d'échec :* on pousse un correctif ; les visiteurs de retour restent
bloqués sur l'ancienne version **même en hard-refresh**, sans autre issue que
vider manuellement les données du site.

### 2.2 — 🟠 Noms de fichiers sans hash + cache-first = JS périmé garanti
`sw.js:2-17,36`

Filenames non versionnés (`product-app.mjs`, …) servis en pur cache-first, sans
revalidation. Même après correction de 2.1, chaque changement d'asset nécessitera
un bump de `CACHE_NAME` **et** un re-fetch du shell. Recommandation : noms
content-hashés, ou stratégie network-first / stale-while-revalidate pour l'app-shell.

### 2.3 — 🟠 `saveDbcs` sans garde de quota
`spikes/pwa-local-engine/browser/product-backend.mjs:200`

`localStorage.setItem(LIBRARY_KEY, …)` stocke le texte complet de jusqu'à 20 DBC
(cap ~5 Mo par origine) sans `try/catch`. Un import de gros DBC lève un
`QuotaExceededError` non rattrapé qui casse le flux d'import. À noter :
`workspace.mjs` gère correctement ce cas (`:124-129`) mais est du code mort non
importé.

### 2.4 — 🟡 Manifest sans icônes raster
`spikes/pwa-local-engine/site/manifest.webmanifest:10-17`

Seule icône : un SVG `sizes: "any"`. Les critères d'installabilité Chrome et les
icônes home-screen iOS/Android exigent généralement du PNG 192×192 et 512×512. Le
PWA risque de ne pas être installable et d'afficher une icône cassée.

### 2.5 — 🟢 Posture de sécurité hosting : saine
Pas de secret, pas de `localhost`/host absolu, aucun `fetch`/XHR/WebSocket réel
(tous les `/api/...` sont servis par un backend embarqué en mémoire via
`product-app.mjs:98` → table de routes `product-backend.mjs`). CSP stricte et
cohérente (`index.html:6`), pas de `url()`/`@import`/CDN en CSS, chemins relatifs
partout (`./…`) donc sûrs sous un sous-chemin, SW enregistré avec scope correct
(`product-app.mjs:1730`).

## 3. Parité du moteur navigateur vs oracle Python

Base saine : les `.mjs` compilés sont des copies fidèles des `.ts` (le build ne
fait que blanchir les annotations de type) — **aucune dérive source/build**.
`browser/product-app.mjs` (70 Ko) n'a en revanche pas de contrepartie `src` ni
d'oracle pour se comparer.

### 3.1 — 🔴 Les IDs étendus (29 bits) ne décodent jamais
`spikes/pwa-local-engine/src/dbc.ts:14-20`

`loadText` stocke `arbitration_id: Number(bo[1])` verbatim et câble
`is_extended_id: false`. En DBC, un message étendu porte le bit `0x80000000` dans
l'id de la frame `BO_`, et l'id réel est `frame_id & 0x7FFFFFFF` (cf. oracle
`dbc.py:63-64`).

*Scénario :* `BO_ 2364540158 EEC1` (=0x8CF004FE) est stocké tel quel ; la frame ASC
arrive avec `arbitration_id = 0x0CF004FE` et `is_extended_id = true` → jamais de
correspondance → **toute trace J1939 / 29 bits ressort en `unknown_id`** côté
navigateur alors qu'elle décode côté Python.

### 3.2 — 🔴 Signaux Motorola / big-endian non supportés
`spikes/pwa-local-engine/src/decode.ts:69`

`extractSignal` lève `"Motorola byte order is outside this spike"`. Tout signal
`@0` (big-endian) → exception → frame entière en `decode_error` → **tous** ses
signaux perdus. cantools décode les deux ordres d'octets (`decode.py:49`).

### 3.3 — 🔴 Multiplexage ignoré
`spikes/pwa-local-engine/src/dbc.ts:4`, `src/decode.ts:32`

Le token multiplexeur (`m<n>`/`M`) est consommé mais jeté ; `decode.ts` boucle sur
tous les signaux du message sans filtrer par valeur de mux. Résultat : émission de
signaux absents de la frame, avec des valeurs lues sur les bits de l'autre groupe.

### 3.4 — 🟠 `locateRow` : sémantique divergente
`spikes/pwa-local-engine/src/store.ts:315-320`

Renvoie la première ligne `timestamp_s >= at` (et `null` au-delà de la dernière),
au lieu de la ligne au `abs(timestamp - at)` minimal (Python `store.py:752-766`,
toujours non-null s'il y a des lignes). Le clic graphe→trace (AC3) tombe sur la
mauvaise ligne, ou ne renvoie rien au-delà de la dernière frame.

### 3.5 — 🟠 DBC dupliqués identiques → `unknown_id`
`spikes/pwa-local-engine/src/dbc.ts:52-67`

Quand un id a >1 message sans entrée `resolution`, il est exclu de l'index même si
les définitions sont identiques (Python `_pick` renvoie `entries[0]` et décode).
Charger deux fois le même DBC rend ces frames indécodables côté navigateur.

### 3.6 — 🟡 Écarts moyens divers
- `asc.ts:173-176` : `parseInt` permissif accepte des IDs/octets malformés que
  `int(token, base)` Python rejette → divergence sur toute ligne « sale ».
- `store.ts:255-305` : filtres `trace_rows` divergents (events non exclus hors
  filtre `signal`, `id_hex` en égalité exacte au lieu de sous-chaîne, case).
- `store.ts:125-147` : `signalSeries` n'exclut pas les valeurs non numériques et
  décime par stride d'index au lieu de min/max par bucket → les pics disparaissent
  sur les graphes décimés ; `maxPoints` par défaut 50 000 vs 4000 côté Python.
- `store.ts:162-166` : `signalStats` renvoie `message`/`signal`/`total` au lieu de
  `message_name`/`signal_name`/`count` → un consommateur calé sur le contrat Python
  lit `undefined`.
- `decode.ts:19,68` : critères de `decode_error` et limite 52 bits différents de
  cantools (support 64 bits, `allow_truncated=False`).

## 4. Régressions dans le produit FastAPI (vérifiées)

### 4.1 — 🔴 `/api/trace` renvoie 500 au premier chargement
`src/cantracediag/api.py:764`, `src/cantracediag/store.py:675-720`

`api_trace` passe `cursor` (str|None) en 1ᵉʳ argument positionnel de
`store.trace_rows(...)`, dont le 1ᵉʳ paramètre est resté `offset: int`. Avec
`cursor=None` → `int(None)` dans le `OFFSET` → `TypeError` non rattrapé (le handler
ne catch que `ValueError`) → **HTTP 500**. La pagination keyset
(`next_cursor`/`prev_cursor`/`start_index`) attendue par `trace.js:39-47` n'est
implémentée nulle part. *Confirmé par lecture du code.*

### 4.2 — 🔴 Le middleware sécurité bloque quasiment tout le trafic de test
`src/cantracediag/security.py:111-114`, `src/cantracediag/api.py:216-219`

L'allowlist `Host` ne contient que du loopback (`localhost`, `127.0.0.1`, `::1`).
Tout autre `Host` → 403 avant handler. La suite de tests part en **28 échecs / 21
passés** (TestClient envoie `Host: testserver`), donc **toutes les nouvelles
features sont non testées de bout en bout**. `security.py` couvre
Host/Origin/token/cap upload mais **pas** le path traversal (toujours `_safe_name`).
*Confirmé : allowlist loopback-only.*

### 4.3 — 🟠 `app.js` (1431 lignes) : code mort, modifié et cassé
`src/cantracediag/web/app.js`

`index.html` ne charge plus que les modules `js/*.js` (core, import, signals, plot,
report, trace, inspector, main) — plus aucune référence à `app.js`. Or `app.js` a
reçu +141 lignes (`refreshStats`, `openReportDialog`, `runExport`) qui référencent
des IDs **inexistants** dans le nouvel `index.html` (`statsReadout`, `reportBtn`,
`reportDialog` → 0 occurrence). À supprimer : contradictoire et trompeur. La version
modulaire (`report.js:97`) utilise correctement `withToken(...)` là où le
`runExport` mort faisait un `fetch` sans token (401). *Confirmé.*

### 4.4 — 🟢 Points sains
Maths `signal_stats` correctes (`store.py:349-419` : `stddev_samp` sur n=1 → None,
RMS = `sqrt(avg(v²))` sur `value_num` non nul, branche numérique/texte).
`export.wide_csv` correct (s'appuie sur l'`ORDER BY` de `iter_export_batches`,
schéma valide même sur sélection vide).

### 4.5 — 🟡 Couverture de tests
- `POST /api/cursors` (`api.py:722`) sans test.
- Pas de test HTTP pour `csv_wide` (scope/format), seulement l'unité `wide_csv`.
- Aucun test n'assure la forme keyset de la réponse trace — d'où le passage de 4.1.

## 5. Recommandation de séquencement avant hébergement

1. **Committer d'abord** — rien n'est versionné. Découper au minimum : (a) features
   produit FastAPI, (b) promotion du PWA hors de `spikes/`.
2. **Corriger le produit FastAPI** (4.1, 4.2, 4.3) pour repasser les tests au vert :
   c'est l'oracle de parité, il doit être fiable avant tout portage.
3. **Boucler la parité moteur navigateur** (3.1, 3.2, 3.3) : sans IDs étendus,
   Motorola et mux, la version full frontend donne des résultats faux sur des traces
   réelles — pire qu'un backend.
4. **Réparer le cycle de vie du SW** (2.1, 2.2) : sinon le site devient
   non-corrigeable après le 1ᵉʳ déploiement.
5. **Détails d'installabilité** : icônes PNG 192/512, garde de quota sur `saveDbcs`.
