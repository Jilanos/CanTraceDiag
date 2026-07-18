## req_003_robustesse_execution_et_completude_post_audit_2026_07_16 - Robustifier et compléter CanTraceDiag après audit du 16 juillet 2026
> From version: 1.0.0
> Schema version: 1.0
> Status: Obsolete
> Understanding: 100%
> Confidence: 100%
> Complexity: high
> Theme: quality-hardening
> Reminder: Update status/understanding/confidence and linked backlog/task references when you edit this doc.
> Non-semantic edit: Linked backlog item_008 for the P0 execution-robustness slice; no scope change.
> Owner: codex-worka

# Needs
- Rendre l'import réellement asynchrone : il ne doit plus geler l'API, doit exposer une
  progression continue par phases et être annulable effectivement.
- Éliminer les courses d'état de session : aucun remplacement de store ne doit casser
  une requête en cours, et la session précédente doit survivre jusqu'au succès validé
  du nouvel import.
- Rendre les erreurs visibles et actionnables dans l'UI : plus aucun échec réseau
  silencieux ne doit bloquer le chargement, figer la table ou laisser une checkbox
  incohérente ; le dialog de conflit DBC doit toujours avoir une issue de secours.
- Ramener les endpoints chauds (curseur, pagination trace, séries) à un coût borné,
  avec une pagination stable et déterministe.
- Livrer l'export des données (CSV et Parquet) sur la sélection de signaux et la plage
  entre curseurs, ainsi que les statistiques entre curseurs et un rapport d'import
  global des résolutions DBC.
- Restreindre la surface réseau locale : l'API ne doit pas être exploitable par DNS
  rebinding ni servir de lecteur de fichiers arbitraires.
- Corriger le responsive 1280x720 / 1024x768, l'accessibilité des favoris, filtres et
  lignes de table, et offrir un thème clair.
- Réduire la dette : parsing ASC robuste aux lignes tronquées et timestamps négatifs,
  code mort supprimé, dépendances justifiées, `app.js` modularisé sans casser les E2E.

# Context
- L'audit complet est documenté dans `docs/audit-complet-2026-07-16.md` (version
  auditée `8428922`), en continuité de `docs/audit-bout-en-bout-2026-07-15.md`.
- Le lot P0 de req_002 (confiance DBC, XSS, CI) est corrigé et testé : 63 tests verts.
- Constats bloquants restants : `api_import_files` exécute le décodage dans l'event
  loop (`api.py:252-297`) ; l'annulation d'import est factice (`api.py:436-441`) et
  l'UI n'interroge jamais `/api/import-job` ; `replace_store` peut fermer le store
  DuckDB sous des requêtes concurrentes (`api.py:83-94`) ; `nearest_sample` fait un
  full scan par survol (`store.py:292-312`) ; la pagination trie sur `timestamp_s`
  seul et recalcule `count(*)` à chaque page (`store.py:342-399`) ; un seul
  `/api/series` en échec bloque tout `onLoaded` (`app.js:296-326`) ; Échap ferme le
  dialog de conflit sans réouverture possible (`app.js:170-203`).
- L'export CSV/Parquet (backlog P1, roadmap Phase 4) n'existe pas ; `pyarrow` et
  `python-can` sont déclarés mais jamais importés.
- `/api/import` lit des fichiers arbitraires sans vérification `Host`/`Origin` ;
  `serve --host 0.0.0.0` expose l'API au LAN sans auth.
- Le flush d'ingestion ne borne pas `sample_batch` (`pipeline.py:87`) : jusqu'à ~3 M
  de dicts en RAM pour des messages riches en signaux.
- Le README annonce une table « virtualisée » (c'est une pagination) et 54 tests (63).

# Product decisions
- Le premier lot livre ensemble l'import asynchrone réel (progression + annulation
  effective + préservation de session) et la sûreté de concurrence : ce sont deux
  faces du même risque d'exécution et ils se testent ensemble.
- La gestion d'erreurs frontend passe par un helper unique (journalisation console +
  zone de statut UI) ; les erreurs non-réseau ne sont jamais avalées silencieusement.
- L'export vise le workflow diagnostic : signaux sélectionnés et plage [A,B] en CSV et
  Parquet, en flux depuis DuckDB, sans matérialisation complète en RAM.
- La pagination trace passe en tri stable `(timestamp_s, seq)` ; le keyset est préféré
  à OFFSET là où l'UI le permet, et le total est mis en cache par jeu de filtres.
- La sécurité locale suit le modèle Jupyter : `TrustedHostMiddleware`, token de
  session généré au lancement, plafond de taille d'upload ; pas d'authentification
  multi-utilisateur.
- Le thème clair réutilise les variables CSS existantes via `prefers-color-scheme`
  sans refonte visuelle ; le tactile passe aux Pointer Events sans viser une
  expérience mobile complète.
- La modularisation d'`app.js` préserve une surface de test explicite
  (`window.__ctd`) pour les E2E existants ; pas de framework.

# Priorities
- P0 - Robustesse d'exécution, livrée en un seul bloc : import hors event loop avec
  progression par phases et annulation effective, flush `sample_batch` borné,
  verrouillage du cycle de vie de session, préservation de la session précédente
  jusqu'au succès, gestion d'erreurs UI unifiée, issue de secours du dialog de
  conflit, polling de progression côté UI.
- P1 - Performance des endpoints chauds : curseur borné, pagination stable et keyset,
  index ou clé signal pour les séries, endpoint curseur batch, commit atomique des
  séries côté front, cache des couleurs et coalescence rAF du rendu.
- P1 - Complétude diagnostic : export CSV/Parquet (sélection + plage [A,B]),
  statistiques entre curseurs, rapport d'import global des résolutions DBC, saut
  « aller à t= » dans la trace.
- P1 - Sécurité locale : TrustedHost + token de session, plafond d'upload,
  vérification Origin, messages d'erreur sans oracle de chemins.
- P2 - UI, design et accessibilité : thème clair, favoris/filtres/lignes de table
  accessibles, responsive 1280x720 et 1024x768 testé, Pointer Events, états vides,
  documentation des raccourcis dans l'UI.
- P2 - Dette et maintenabilité : parsing ASC robuste (lignes tronquées, timestamps
  négatifs/scientifiques, DLC > 8), code mort supprimé, dépendances justifiées ou
  retirées, `_id_hex` factorisé, `app.js` modularisé, tests CLI, budget perf
  synthétique en CI, E2E non skippables silencieusement en CI, README resynchronisé.

# Acceptance criteria
- AC1: Pendant l'import d'une trace volumineuse, `/api/import-job` répond en moins de
  200 ms, expose des phases (upload, parsing, décodage, indexation) et une progression
  mesurée sur les octets ou trames traités ; un test le prouve avec une trace
  synthétique.
- AC2: L'annulation interrompt réellement le pipeline en moins d'un flush de lot,
  laisse la session dans un état cohérent et se reflète dans l'UI ; un job annulé
  n'est plus déclaré annulable.
- AC3: Un import qui échoue ou est annulé laisse la session précédente intacte et
  interrogeable ; le remplacement de store est atomique et aucun test de rafale
  concurrente ne produit d'erreur de connexion fermée.
- AC4: `sample_batch` est borné par la même limite de lot que frames et événements ;
  un test d'ingestion avec un message multi-signaux le vérifie.
- AC5: `/api/cursor` n'exécute plus de scan complet (plan de requête borné ou mesure
  comparative testée) et un endpoint batch renvoie les valeurs de N signaux × 2
  curseurs en un appel utilisé par l'UI.
- AC6: La pagination de la trace est stable et déterministe : tri `(timestamp_s,
  seq)`, aucune ligne dupliquée ni manquante entre pages consécutives, `locate_row`
  cohérent avec la page servie ; testé sur des rafales au même timestamp.
- AC7: L'échec d'un `/api/series` au chargement ou au toggle n'empêche ni le rendu du
  plot ni la table ; l'erreur est visible dans l'UI, la checkbox reste cohérente, et
  plus aucun `catch` vide ne subsiste dans `app.js`.
- AC8: Le dialog de conflit DBC fermé par Échap peut être rouvert par un contrôle
  visible tant que la résolution est en attente ; testé en E2E.
- AC9: L'export CSV et Parquet couvre les signaux sélectionnés et la plage [A,B],
  fonctionne en flux (mémoire bornée, testé), et les statistiques min/max/moyenne/
  écart-type sur [A,B] sont affichées par signal.
- AC10: Un rapport d'import accessible depuis l'UI liste, par ID arbitré, la DBC
  retenue et l'origine de la décision (auto-équivalence ou choix opérateur).
- AC11: L'API rejette les requêtes dont le Host n'est pas dans l'allowlist locale et
  exige le token de session sur les endpoints mutateurs ; l'upload a un plafond de
  taille configurable ; des tests hostiles couvrent DNS rebinding et dépassement.
- AC12: Aucun contrôle principal ne déborde à 1280x720 ni 1024x768 (testé en E2E) ;
  favoris, filtres et lignes de table sont utilisables au clavier avec noms
  accessibles ; un thème clair suit `prefers-color-scheme`.
- AC13: Une ligne ASC tronquée ou avec attributs de fin de ligne produit un événement
  ou statut explicite (jamais un silence ni une trame corrompue) ; les timestamps
  négatifs et en notation scientifique sont acceptés ; le DLC CAN classique est borné
  à 8.
- AC14: `pyarrow` et `python-can` sont utilisés ou retirés ; le code mort identifié
  par l'audit est supprimé ; `app.js` est découpé en modules ES et les E2E passent via
  la surface `window.__ctd` ; le README reflète la pagination réelle et le nombre de
  tests.
- AC15: La CI échoue si les E2E sont skippés faute de navigateur, et protège un budget
  synthétique réduit de temps et de mémoire d'import.

# Suggested implementation slices
- Slice 1: Import asynchrone réel (thread + progression + annulation), flush borné,
  verrou de session, préservation de session, polling UI.
- Slice 2: Gestion d'erreurs UI unifiée, dialog de conflit rouvrable, états vides.
- Slice 3: Endpoints chauds : curseur borné + batch, pagination stable/keyset, index
  signal, commit atomique des séries, optimisations de rendu.
- Slice 4: Export CSV/Parquet, statistiques [A,B], rapport d'import, saut temporel.
- Slice 5: Sécurité locale (TrustedHost, token, plafond upload, Origin).
- Slice 6: Thème clair, accessibilité, responsive 1280/1024, Pointer Events.
- Slice 7: Parsing ASC robuste, dette, modularisation JS, tests CLI, budgets CI.

# Out of scope
- Support BLF/MF4 (seule l'abstraction de lecteur peut être préparée si triviale).
- Replay temps réel, connexion véhicule, multi-bus avancé.
- Collaboration multi-utilisateur, cloud, stockage partagé.
- Réécriture du frontend dans un framework.
- Persistance durable des analyses entre redémarrages serveur (cache/reopen), reportée
  à une requête ultérieure.
- Packaging Windows natif.

# Definition of Ready (DoR)
- [x] Problem statement is explicit and user impact is clear.
- [x] Scope boundaries (in/out) are explicit.
- [x] Acceptance criteria are testable.
- [x] Dependencies and known risks are listed.

# Dependencies and risks
- DuckDB, FastAPI, cantools et l'UI vanilla restent les composants cibles.
- L'import en thread doit composer avec le `RLock` existant de `TraceStore` sans
  réintroduire les instabilités de concurrence corrigées par req_002.
- Le token de session ne doit pas casser le workflow local (URL avec token au
  lancement, comme Jupyter) ni les tests E2E.
- La modularisation d'`app.js` casse potentiellement les E2E qui lisent l'état global :
  la surface `window.__ctd` doit être posée avant le découpage.
- Le keyset de pagination doit rester compatible avec le saut arbitraire de page si
  l'UI le propose ; sinon conserver OFFSET avec total mis en cache.
- Les traces et DBC réelles restent hors dépôt ; les budgets CI utilisent des traces
  synthétiques reproductibles.
- L'export Parquet introduit l'usage réel de `pyarrow` : vérifier l'empreinte de la
  dépendance sous WSL.

# Companion docs
- Product brief(s): `prod_002_product_brief_cantracediag_mvp`
- Architecture decision(s): `adr_002_adr_architecture_cantracediag_mvp`

# References
- `docs/audit-complet-2026-07-16.md`
- `docs/audit-bout-en-bout-2026-07-15.md`
- `req_002_fiabiliser_cantracediag_apres_audit_fonctionnel_ui_et_performance`
- `docs/product-backlog.md`
- `docs/roadmap.md`
- `src/cantracediag/api.py`
- `src/cantracediag/store.py`
- `src/cantracediag/pipeline.py`
- `src/cantracediag/formats/asc.py`
- `src/cantracediag/web/app.js`
- `src/cantracediag/web/index.html`
- `.github/workflows/ci.yml`

# AI Context
- Summary: Harden CanTraceDiag execution robustness (real async import, session
  concurrency, unified UI error handling), bound hot-endpoint costs, deliver
  CSV/Parquet export and cursor statistics, secure the local API surface, then address
  theme, accessibility, responsive and technical debt from the 2026-07-16 audit.
- Keywords: cantracediag, async-import, concurrency, cursor, pagination, export,
  parquet, dns-rebinding, accessibility, responsive, tech-debt
- Use when: Planning or implementing post-audit robustness, performance, export and
  security work.
- Skip when: Work targets BLF/MF4, replay, cloud, collaboration or native packaging.

# Backlog
- `item_008_p0_rendre_execution_robuste_import_asynchrone_session_et_erreurs_ui`
- `item_009_p1_optimiser_endpoints_chauds`
- `item_010_p1_livrer_export_et_completude_diagnostic`
- `item_011_p1_durcir_securite_locale`
- `item_012_p2_ameliorer_ui_accessibilite_responsive`
- `item_013_p2_reduire_dette_parsing_maintenance_ci`

# Links
- Superseded by: `req_007_finaliser_workflow_diagnostic_et_clarifier_cantracediag`
