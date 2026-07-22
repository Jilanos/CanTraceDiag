# Preuve post-audit PWA full frontend - 2026-07-22

Source audit : `docs/audit-refonte-full-frontend-2026-07-22.md`.
Chaine Logics : `req_013_lever_les_bloquants_d_hebergement_pwa_full_frontend_post_audit_2026_07_22`.
Domaine cible : `cantracediag.paulmondou.fr`.

## Decision

**Go conditionnel pour une previsualisation statique controlee. No-go pour un
hebergement public annonce comme produit final tant que les limites `task_021`
restantes ne sont pas levees ou acceptees explicitement.**

Les bloquants techniques de l'audit du 22 juillet 2026 ont ete traites dans la
chaine `req_013` : oracle FastAPI, parite DBC navigateur, service worker/cache,
quota DBC, installabilite PWA et provenance de build. Le deploiement public reste
conditionne a un point de gouvernance produit :

1. `task_021_migrer_l_ui_produit_vers_la_pwa_local_first_avec_parite_mvp` reste
   ouverte pour le jalon MVP large : gros fichiers, stockage durable
   OPFS/IndexedDB et validation produit-scale restent hors de cette gate
   post-audit.

## Corrections livrees

- Provenance : `.gitignore` exclut `spikes/pwa-local-engine/browser/` et
  `spikes/pwa-local-engine/site/` comme artefacts generes ; la strategie
  source/build/commit est documentee.
- FastAPI : `/api/trace` accepte les curseurs keyset opaques de l'UI sans 500
  et retourne `limit`, `start_index`, `next_cursor` et `prev_cursor`.
- Securite : `testserver` est reconnu comme hote in-process TestClient ; les
  tests couvrent encore les refus Host et Origin hostiles.
- Front legacy : `src/cantracediag/web/app.js` a ete supprime pour eviter toute
  confusion avec le front actif modulaire `src/cantracediag/web/js/*.js`.
- Parite DBC navigateur P0 : IDs etendus 29 bits, signaux Motorola/big-endian et
  multiplexage sont couverts par tests.
- Divergences moteur P1 : parsing ASC strict, DBC dupliques identiques,
  `locateRow` nearest, filtres trace, decimation min/max et contrat
  `signalStats` sont alignes ou rendus compatibles.
- PWA statique : `sw.js` recoit un cache name versionne par hash de build,
  navigations en network-first, cache shell stale-while-revalidate, icones PNG
  192/512 et garde de quota DBC active.

## Validations executees

```bash
.venv/bin/python -m pytest tests/test_api.py tests/test_export.py tests/test_diagnostic.py tests/test_workspace.py
```

Resultat : 63 passed, 1 avertissement `StarletteDeprecationWarning`.

Validation post-merge `feat/pwa-local-first` dans `main` :

```bash
.venv/bin/ruff check .
.venv/bin/pytest
```

Resultat : lint OK, 147 passed, 1 avertissement `StarletteDeprecationWarning`.

Validation CI post-merge :

- `092f3cd` (`Merge branch 'feat/pwa-local-first'`) : GitHub Actions CI OK sur
  Python 3.11 et 3.12.
- `bdb08f7` (`ci: update GitHub Actions Node 24 runners`) : GitHub Actions CI
  OK sur Python 3.11 et 3.12 avec `actions/checkout@v7.0.1` et
  `actions/setup-python@v7.0.0`.

```bash
node --test spikes/pwa-local-engine/tests/*.test.ts
```

Resultat : 19 passed.

```bash
node spikes/pwa-local-engine/build-browser.mjs
```

Resultat : build de `spikes/pwa-local-engine/browser/` et
`spikes/pwa-local-engine/site/` reussi.

```bash
CTD_ENGINE_ROOT=spikes/pwa-local-engine/site CTD_ENGINE_PORT=9895 CTD_ENGINE_DEBUG_PORT=9245 node spikes/pwa-local-engine/browser-smoke.mjs
```

Resultat : smoke OK depuis le build statique, import fixture ASC+DBC, vues
workspace, stats A/B, rapport, export CSV wide, manifest PNG 192/512, service
worker actif, cache `cantracediag-pwa-shell-e0ad4cba16870afe`, zero appel
reseau `/api/...`.

```bash
logics-manager lint --require-status
```

Resultat : OK.

```bash
logics-manager flow validate req_013_lever_les_bloquants_d_hebergement_pwa_full_frontend_post_audit_2026_07_22 task_023_orchestrer_la_stabilisation_post_audit_full_frontend task_024_p0_etablir_provenance_et_packaging_de_la_refonte_pwa task_025_p0_restaurer_l_oracle_fastapi_et_les_tests_serveur task_026_p0_corriger_la_parite_dbc_navigateur_sur_traces_reelles task_027_p1_aligner_les_divergences_moteur_navigateur_non_bloquantes task_028_p0_fiabiliser_service_worker_cache_et_installabilite_pwa task_029_p1_produire_le_dossier_de_preuve_go_no_go_hebergement --format json
```

Resultat : OK, 0 finding.

```bash
logics-manager audit --group-by-doc
```

Resultat : echec global attendu sur dette Logics historique hors `req_013` :
`req_004`, `req_005`, `req_006`, `req_012`. Pour la chaine courante, seul le
brief `prod_003` garde un avertissement non bloquant
`companion_doc_missing_mermaid`.

## Limites residuelles

- **Risque traite - gouvernance/provenance Git** : la branche ne doit pas etre
  publiee depuis un working tree non commite. Decision : les commits de jalon
  sont produits par l'agent avant toute publication publique.
- **Risque moyen - task_021 encore ouverte** : la migration MVP large inclut
  encore stockage durable OPFS/IndexedDB, gros fichiers et benchmarks produit.
  Decision : ne pas presenter l'hebergement comme version finale full frontend.
- **Risque moyen - couverture navigateurs** : validation Chromium uniquement.
  Decision : valider Firefox/Safari mobile avant annonce large.
- **Risque moyen - Parquet navigateur** : export Parquet reste differe cote PWA
  statique faute de writer Parquet/WASM valide. Decision : CSV long/wide OK,
  Parquet a annoncer comme limite.
- **Risque bas - audit Logics global** : anomalies historiques hors `req_013`.
  Decision : ne bloquent pas cette gate, mais doivent etre traitees separement
  avant une revendication de corpus Logics globalement sain.

## References Logics

- `task_024_p0_etablir_provenance_et_packaging_de_la_refonte_pwa` : Done.
- `task_025_p0_restaurer_l_oracle_fastapi_et_les_tests_serveur` : Done.
- `task_026_p0_corriger_la_parite_dbc_navigateur_sur_traces_reelles` : Done.
- `task_027_p1_aligner_les_divergences_moteur_navigateur_non_bloquantes` : Done.
- `task_028_p0_fiabiliser_service_worker_cache_et_installabilite_pwa` : Done.
- `task_029_p1_produire_le_dossier_de_preuve_go_no_go_hebergement` : Done.

## Commits de jalon crees par l'agent

- `e84a6b4` - `fix(api): restore diagnostic oracle after frontend audit`
- `4ca44e0` - `feat(pwa): add local-first static browser engine`
- `8727b5a` - `feat(pwa): add 500mb browser scanning spike`

Le commit portant cette preuve et la chaine Logics complete finalise le lot
workflow/documentation.
