## req_014_repondre_a_l_audit_code_du_23_juillet_2026 - Repondre a l audit code du 23 juillet 2026
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90
> Confidence: 85
> Complexity: High
> Theme: Post-audit code hardening
> Reminder: Update status/understanding/confidence and linked backlog/task references when you edit this doc.

# Needs
- Transformer les constats de `docs/audit-code-2026-07-23.md` en un lot de durcissement executable, teste et documente.
- Lever en priorite les risques qui peuvent bloquer l usage local fiable : verrou DuckDB conserve pendant le streaming CSV/wide, fuite possible de chemins locaux dans les erreurs DBC/import et absence de plafond agrege d upload.
- Corriger les regressions de correctness de risque moyen, expliciter les choix de securite local-first restants et nettoyer la dette simple sans elargir vers une refonte API complete.

# Context
- L audit du 23 juillet 2026 a ete realise sur `main` (`7c139c7`) avec `ruff check .` vert et 126 tests Python verts.
- Les erreurs Playwright relevees viennent de l absence locale du binaire Chromium ; elles ne sont pas classees comme defaut code dans l audit.
- Les constats prioritaires sont H1, S1 et S3 ; M1/M2 et S2/S4/S5 forment le second niveau ; L4/L5/L6 et une partie de M3 sont des nettoyages.
- Le produit reste cible local-first mono-utilisateur : les corrections doivent renforcer ce modele sans introduire de serveur multi-utilisateur, d authentification distante ou de confinement fonctionnel non demande.
- La reponse doit produire des preuves reproductibles, notamment tests de concurrence export, non-fuite de chemins, plafond upload agrege et comportement deterministe des filtres/decimation.

# Acceptance criteria
- AC1: H1 est corrige : les exports CSV et CSV wide ne conservent plus le verrou DuckDB pendant toute la consommation HTTP, et un test prouve qu une requete concurrente peut progresser pendant un stream lent.
- AC2: S1 est corrige : les erreurs parse DBC et import serveur ne renvoient plus de chemins locaux bruts via l API, les jobs d import ou l UI, et les cas parse-error/import-failure sont couverts par des tests.
- AC3: S3 est corrige : une requete multi-fichier respecte un plafond agrege documente et teste, en plus des limites par fichier.
- AC4: M1 et M2 sont traites : `_decimate` lie les valeurs flottantes au lieu de les interpoler, les entrees `nan`/`inf`/degeneres sont bornees, et un filtre signal sans correspondance catalogue retourne explicitement zero ligne.
- AC5: Les decisions S2/S4/S5 sont tranchees et documentees : token en query string, lecture locale arbitraire de `/api/import`, et comportement des en-tetes `Host`/`Origin` absents ont soit un correctif code, soit une justification threat model et des tests adaptes.
- AC6: Les nettoyages a faible risque sont faits ou explicitement reportes : purge `series_cache`, tolerance `frame_at`/`frame_signals`, fixture ASC `dlc==0`, doublon `_f`, `iter_asc` mort, helper de streaming store et extraction minimale des closures import.
- AC7: La validation finale inclut `ruff check .`, la suite Python pertinente, les tests cibles ajoutes, et une validation Logics (`lint --require-status` puis `audit --group-by-doc`).

# Definition of Ready (DoR)
- [x] Problem statement is explicit and user impact is clear.
- [x] Scope boundaries (in/out) are explicit.
- [x] Acceptance criteria are testable.
- [x] Dependencies and known risks are listed.

# Companion docs
- Product brief(s): (none yet)
- Architecture decision(s): (none yet)

# References
- `docs/audit-code-2026-07-23.md`
- `src/cantracediag/api.py`
- `src/cantracediag/store.py`
- `src/cantracediag/security.py`
- `src/cantracediag/formats/asc.py`
- `src/cantracediag/pipeline.py`
- `src/cantracediag/cli.py`
- `tests/test_api.py`
- `tests/test_security.py`
- `tests/test_export.py`
- `tests/test_trace_nav.py`
- `tests/test_asc.py`

# AI Context
- Summary: Repondre aux constats H1/S1/S3/M1/M2/S2/S4/S5 de l audit code du 23 juillet 2026.
- Keywords: post-audit, code-hardening, duckdb-streaming, sanitized-errors, upload-limits, local-first-security
- Use when: Implementing or reviewing the code hardening requested by `docs/audit-code-2026-07-23.md`.
- Skip when: The change targets only the PWA full-frontend post-audit chain already covered by `req_013`.

# Backlog
- `item_029_repondre_a_l_audit_code_du_23_juillet_2026`
