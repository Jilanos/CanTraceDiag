# Provenance PWA full frontend post-audit - 2026-07-22

Source audit: `docs/audit-refonte-full-frontend-2026-07-22.md`.
Chaine Logics: `req_013_lever_les_bloquants_d_hebergement_pwa_full_frontend_post_audit_2026_07_22`.

## Objectif

La refonte full frontend ne doit pas etre hebergee depuis un artefact de spike non
versionne. Cette note classe les fichiers a suivre, les fichiers generes et les
lots commit-ready attendus avant une decision de deploiement.

## Classification des fichiers

### Sources a versionner

- `spikes/pwa-local-engine/src/*.ts` : moteur navigateur ASC/DBC, backend local,
  store et workspace.
- `spikes/pwa-local-engine/build-browser.mjs` : script de build statique.
- `spikes/pwa-local-engine/*.md` : resultats, decisions de stockage et notes de
  deploiement du spike PWA.
- `spikes/pwa-local-engine/assets/` : assets sources de la PWA.
- `spikes/pwa-local-engine/manifest.webmanifest` et
  `spikes/pwa-local-engine/sw.js` : sources du manifest et du service worker.
- `spikes/pwa-local-engine/tests/*.test.ts` et
  `spikes/pwa-local-engine/browser-smoke.mjs` : tests navigateur/local et smoke.
- `src/cantracediag/web/index.html`, `src/cantracediag/web/styles.css`,
  `src/cantracediag/web/js/*.js` et `src/cantracediag/web/app-icon.svg` :
  shell produit reutilise par le build PWA.
- `src/cantracediag/api.py`, `src/cantracediag/store.py`,
  `src/cantracediag/security.py`, `src/cantracediag/export.py` et tests Python :
  oracle FastAPI et fonctionnalites diagnostic conservees pendant la migration.
- `docs/audit-refonte-full-frontend-2026-07-22.md`, cette note de provenance et
  les documents Logics `req_013`, `item_023` a `item_028`, `task_023` a
  `task_029`.

### Artefacts generes a ne pas versionner comme source de verite

- `spikes/pwa-local-engine/browser/` : modules `.mjs` generes depuis
  `spikes/pwa-local-engine/src/*.ts` et le front produit modulaire.
- `spikes/pwa-local-engine/site/` : repertoire deployable genere. Il peut etre
  archive comme preuve de release, mais ne doit pas etre le seul etat versionne
  d'un deploiement.
- Caches locaux : `.pytest_cache/`, `.ruff_cache/`, `.pw-libs/`, `.venv/`,
  `__pycache__/`.

### Donnees locales a ignorer

- Traces et bases locales : `*.asc`, `*.blf`, `*.mf4`, `*.dbc`, `*.parquet`,
  `*.duckdb`, `data/`, `traces/`.
- Exception volontaire : `tests/fixtures/*.asc` et `tests/fixtures/*.dbc` restent
  versionnables comme fixtures synthetiques anonymisees.

## Build reproductible

Commande de reference depuis la racine du depot :

```bash
node spikes/pwa-local-engine/build-browser.mjs
```

Cette commande :

1. Strippe les sources TypeScript de `spikes/pwa-local-engine/src/` vers
   `spikes/pwa-local-engine/browser/*.mjs`.
2. Genere `browser/product-app.mjs` depuis `src/cantracediag/web/js/*.js`.
3. Regenerere completement `spikes/pwa-local-engine/site/`.
4. Copie le manifest, le service worker, les styles et les assets necessaires au
   serveur statique.

Le repertoire `site/` doit donc etre reconstruit pour validation et deploiement,
pas edite a la main.

## Lots de commits agents recommandes

1. **Oracle FastAPI** : `src/cantracediag/api.py`, `store.py`, `security.py`,
   `export.py`, `src/cantracediag/web/js/`, `styles.css`, tests Python et
   documentation associee.
2. **Source PWA local-first** : `spikes/pwa-local-engine/src/`, `assets/`,
   `manifest.webmanifest`, `sw.js`, `build-browser.mjs`, tests et smoke.
3. **Preuves et workflow** : audit, provenance, resultats de validation,
   `logics/` et context-pack.

Quand l'utilisateur demande d'executer la chaine ou une grosse etape projet,
l'agent cree ces commits lui-meme. Le decoupage reste volontairement par jalon
coherent, pas par micro-changement.

## Gate task_021

`task_021_migrer_l_ui_produit_vers_la_pwa_local_first_avec_parite_mvp` reste le
jalon MVP PWA large. Elle ne doit pas etre fermee comme hebergeable tant que les
P0 de `req_013` ne sont pas resolus ou explicitement supersedes :

- `task_024` provenance et packaging.
- `task_025` oracle FastAPI et tests serveur.
- `task_026` parite DBC navigateur sur traces reelles.
- `task_028` service worker, cache, quota et installabilite PWA.
