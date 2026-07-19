## req_007_finaliser_workflow_diagnostic_et_clarifier_cantracediag - Finaliser le workflow diagnostic et clarifier CanTraceDiag
> From version: 0.1.0
> Schema version: 1.0
> Status: Done
> Understanding: 100%
> Confidence: 100%
> Complexity: high
> Theme: product-clarity-and-diagnostic-completeness
> Reminder: Update status/understanding/confidence and linked backlog/task references when you edit this doc.

# Needs
- Fermer le workflow diagnostic : l'utilisateur doit pouvoir qualifier l'import,
  mesurer une plage entre curseurs, puis exporter les resultats sans quitter
  CanTraceDiag.
- Clarifier la hierarchie de l'interface afin que l'etat courant, l'action principale,
  les filtres actifs et les erreurs restent comprehensibles dans un poste de travail
  dense.
- Garantir une navigation fluide et deterministe sur les traces volumineuses, en
  particulier pour les curseurs, la pagination et la localisation temporelle.
- Durcir l'API locale contre le DNS rebinding, les appels d'origine non attendue, les
  mutations sans jeton et les uploads sans limite.
- Preserver l'integrite de la trace : une ligne ASC invalide, tronquee ou incoherente
  ne doit jamais devenir silencieusement une trame valide.
- Rendre les controles principaux utilisables au clavier et sans debordement aux
  formats desktop cibles, puis reduire la dette frontend et documentaire qui ralentit
  les evolutions suivantes.

# Context
- Baseline inspectee le 18 juillet 2026 sur `main` : import ASC, multi-DBC avec
  resolution de conflits, decodage a la demande, DuckDB local, graphes empiles,
  curseurs A/B, vue trace filtree, inspecteur, bibliotheque DBC, reprise de session,
  progression et annulation d'import sont livres.
- Validation de la baseline dans un environnement `uv` isole : 72 tests passent,
  11 E2E sont skippes faute de Chromium, et `ruff check .` passe.
- L'ancien environnement `.venv` local est inutilisable car ses executables Python
  sont vides ; la reproductibilite de l'environnement developpeur doit etre retablie
  sans versionner le virtualenv.
- `req_003_robustesse_execution_et_completude_post_audit_2026_07_16` a correctement
  declenche les lots de robustesse deja livres, mais son contexte continue de decrire
  ces correctifs comme absents. Les slices encore ouvertes (`task_009` a `task_013`)
  sont des dependances ou des points de reprise, pas une preuve que les fonctions
  deja livrees doivent etre reimplementees.
- L'interface actuelle concentre import, statut, signaux, graphes, curseurs, filtres,
  table et inspecteur sur un seul plan visuel. Elle alterne anglais et francais, et
  les erreurs de sous-composants remplacent le resume global de session.
- Les couts encore non bornes sont visibles dans `TraceStore.nearest_sample`, qui trie
  par distance absolue, et dans `trace_rows`/`locate_row`, qui recalculent le total et
  reposent sur un tri par timestamp seul avec pagination `OFFSET`.
- Le parseur ASC n'accepte pas les timestamps negatifs/scientifiques et ne verifie
  pas explicitement que le nombre d'octets correspond au DLC annonce.
- `pyarrow` et `python-can` sont declares mais non utilises. Le frontend reste compose
  d'un `app.js` global d'environ 1 290 lignes et de CSS embarque dans `index.html`.

# Product decisions
- Conserver l'identite visuelle « instrument de mesure » et la densite desktop ; la
  clarification passe par une hierarchie de modes et d'etats, pas par une page
  marketing ni une simplification qui masque les donnees utiles.
- Structurer l'espace de travail en trois onglets centraux explicites : `Analysis`
  (signaux, graphes, curseurs, statistiques), `Trace` (filtres, table, navigation,
  inspecteur) et `Report` (synthese d'import, DBC utilisees, anomalies, duree et
  exports). L'explorateur de signaux et l'etat de session persistent entre les onglets.
- Utiliser exclusivement l'anglais pour l'interface, les actions, les messages
  utilisateur, les etats vides et la documentation utilisateur. Les statuts techniques
  d'API conservent leur valeur brute en anglais et recoivent un libelle explicite.
- L'export cible d'abord les signaux selectionnes et la plage ordonnee delimitee par
  A/B. CSV et Parquet sont generes en flux depuis DuckDB sans materialisation complete
  en memoire.
- Le format long (`timestamp`, `message`, `signal`, `value`, `unit`) est le schema
  canonique CSV/Parquet. Un CSV large optionnel aligne les timestamps sans interpolation
  et laisse les valeurs absentes vides.
- Les statistiques de plage minimales sont nombre d'echantillons, minimum, maximum,
  moyenne, ecart-type et RMS pour chaque signal numerique selectionne.
- Les signaux textuels ou enumeres affichent le nombre d'echantillons et la repartition
  des valeurs, sans statistiques numeriques artificielles.
- La navigation de trace reste serveur : ordre canonique `(timestamp_s, seq)`,
  curseurs de page opaques et recherche bornee avant/apres un timestamp. L'UI ne
  charge jamais toute l'acquisition.
- La securite suit un modele d'application locale type Jupyter : hote local par
  defaut, allowlist Host, controle Origin, jeton de session pour les mutations et
  taille maximale configurable. En mode LAN, le jeton protege toute l'API et l'import
  par chemin serveur est desactive.
- Conserver Python, FastAPI, DuckDB et le frontend natif. La modularisation JavaScript
  ne doit pas introduire de framework et expose une surface E2E stable
  `window.__ctd`.

# Priorities
- P0 - Confiance et sortie diagnostic : rapport d'import, export CSV/Parquet,
  statistiques A/B, erreurs contextualisees et integrite du parsing ASC.
- P0 - Securite locale : Host, Origin, jeton des mutations, plafond d'upload et
  restriction documentee de l'import par chemin serveur.
- P1 - Clarte du parcours : vues Analysis/Trace/Report, interface tout en anglais,
  criteres actifs visibles, etats vides et presets de disposition.
- P1 - Performance : curseur borne et batch, ordre stable, pagination par curseur,
  localisation coherente et budgets de performance reproductibles.
- P2 - Accessibilite et maintenabilite : clavier, Pointer Events, responsive desktop,
  modules frontend, dependances nettoyees et documentation Logics resynchronisee.

# Acceptance criteria
- AC1: Une vue `Report` fournit une synthese de l'import avec le fichier analyse, la
  plage temporelle et sa duree, les DBC effectivement utilisees, le nombre de trames,
  d'evenements et d'IDs, ainsi que les anomalies regroupees par type (`unknown_id`,
  `ambiguous_id`, `decode_error` et anomalies ASC). Elle est accessible depuis l'etat
  global sans imposer un inventaire detaille par ID.
- AC2: L'utilisateur exporte en CSV et Parquet les signaux selectionnes sur la plage
  explicitement choisie dans le dialogue : `Between A and B`, `Visible window` ou
  `Full trace`. Le format long canonique est disponible en CSV et Parquet ; un CSV
  large optionnel n'interpole pas les signaux. L'export est streame et un test prouve
  que la memoire ne croit pas avec le nombre total de lignes exportees.
- AC3: La vue `Analysis` affiche par signal numerique selectionne le nombre
  d'echantillons, le minimum, le maximum, la moyenne, l'ecart-type et le RMS entre A
  et B. Pour un signal textuel ou enumere, elle affiche le nombre d'echantillons et la
  repartition des valeurs. Les unites et l'absence de donnees sont explicites.
- AC4: L'interface propose les onglets `Analysis`, `Trace` et `Report` sans perdre
  l'etat courant ; l'explorateur de signaux et le statut de session restent presents.
  A 1600x900, l'action principale et le statut sont identifies en moins d'un niveau de
  navigation, et les presets `Plots`, `Trace` et `Full diagnostic` restaurent des
  layouts persistants.
- AC5: Tous les libelles, actions, messages, etats vides et contenus de documentation
  utilisateur sont en anglais. Les statuts techniques disposent d'un libelle anglais
  comprehensible et leur valeur brute reste disponible pour l'audit.
- AC6: Une erreur de serie, table, inspecteur ou export est affichee dans le composant
  concerne avec une action de relance quand elle est pertinente. Elle ne remplace pas
  le resume global, ne bloque pas les autres composants et ne laisse pas un controle
  dans un etat incoherent ; les chemins sont couverts en E2E.
- AC7: La trace affiche un etat vide distinct pour « aucune trace », « aucun resultat
  pour ces filtres » et « chargement impossible ». Les filtres actifs sont visibles,
  supprimables individuellement, persistants, et les filtres secondaires peuvent etre
  replies sans perdre leur valeur.
- AC8: La recherche du point le plus proche utilise au plus une requete bornee avant
  et une apres le timestamp. Un endpoint batch renvoie N signaux pour A et B en un
  appel, et un benchmark synthétique empeche toute regression vers un scan complet.
- AC9: La trace est ordonnee par `(timestamp_s, seq)` et paginee par curseur opaque.
  Sur un fixture contenant plusieurs frames et evenements au meme timestamp, aucune
  ligne n'est dupliquee ou omise et `trace-locate` ouvre la page contenant exactement
  la ligne retournee.
- AC10: L'API rejette un Host ou une Origin non autorises, exige un jeton de session
  sur les endpoints mutateurs en boucle locale et sur tous les endpoints en mode LAN,
  limite la taille d'upload via une configuration documentee et n'expose pas de chemin
  local dans ses messages d'erreur. Des tests hostiles couvrent chaque cas.
- AC11: L'import par chemin serveur est desactive hors boucle locale ou derriere une
  option explicite protegee. Le lancement `--lan` ne rend jamais la lecture arbitraire
  de fichiers accessible sans jeton.
- AC12: Une ligne ASC horodatee mais tronquee, un payload plus court ou plus long que
  le DLC, un octet hors plage ou un DLC CAN classique superieur a 8 produit un
  evenement d'import explicite et aucune trame corrompue. Les timestamps negatifs et
  scientifiques sont acceptes et testes.
- AC13: Les favoris, filtres, onglets, lignes de table, dialogues et redimensionneurs
  sont nommes et utilisables au clavier. Les interactions de graphe et de resize
  utilisent les Pointer Events sans regression souris ; une verification automatisee
  d'accessibilite couvre les parcours principaux.
- AC14: Aucun controle principal ne deborde a 1024x768, 1280x720 et 1600x900. A
  390x844, le support reste minimal : import, chargement, selection d'onglet, filtres
  principaux et export restent accessibles sans promettre l'espace de travail complet.
  Les E2E executent ces quatre viewports et echouent en CI si Chromium ne peut pas se
  lancer au lieu de passer par skip silencieux.
- AC15: `app.js` et le CSS embarque sont decoupes par domaines `core`, `import`,
  `signals`, `plot`, `trace`, `report` et `inspector`, sans framework. Les tests
  navigateur utilisent uniquement la surface explicite `window.__ctd`.
- AC16: `pyarrow` est utilise par l'export Parquet ou retire ; `python-can` est retire
  tant qu'aucun format ne l'utilise ; le code mort et les helpers dupliques sont
  supprimes. La suite complete, le lint et un budget synthétique temps/memoire passent
  sur Python 3.11 et 3.12.
- AC17: Le README, la roadmap, le backlog produit et les documents Logics ne
  presentent plus les fonctions deja livrees comme manquantes. Chaque AC de cette
  requete est relie a une task avec preuve, `logics-manager lint` passe et l'audit ne
  remonte aucun blocage nouveau pour cette chaine.

# Suggested delivery slices
- Slice 1 - Synthese d'import, statistiques A/B et exports CSV/Parquet : AC1-AC3.
- Slice 2 - Endpoints chauds et navigation deterministe : AC8-AC9.
- Slice 3 - Securite locale et import par chemin : AC10-AC11.
- Slice 4 - Integrite ASC : AC12.
- Slice 5 - Accessibilite et responsive minimal : AC13-AC14.
- Slice 6 - Modularisation, dependances, CI et documentation technique : AC15-AC17,
  hors changements de hierarchie visuelle reserves a la slice finale.
- Slice 7 - Clarte UI finale : onglets Analysis/Trace/Report, anglais integral,
  erreurs contextualisees, filtres actifs, etats vides et presets : AC4-AC7.
- Chaque slice est livree dans un commit autonome comprenant implementation, tests et
  documentation associee. Aucun commit ne melange deux slices ; la slice 7 termine la
  sequence afin que la refonte de clarte repose sur les contrats fonctionnels et les
  modules stabilises par les six commits precedents.

# Out of scope
- Replay temps reel, connexion a un vehicule ou emission de trames CAN.
- Collaboration multi-utilisateur, cloud ou stockage partage.
- Reecriture du frontend avec React, Vue ou un framework equivalent.
- Packaging Windows natif dans cette requete.
- Support produit BLF/MF4, multi-bus, comparaison de deux traces, annotations,
  signaux calcules, recherche de payload masquee et superposition multi-axe. Ces
  options doivent etre re-evaluees apres mesure de l'usage du workflow finalise.
- Reimplementation de l'import asynchrone, de l'annulation, de la bibliotheque DBC
  ou de la reprise de session deja livres, hors correction d'une regression prouvee.

# Definition of Ready (DoR)
- [x] Problem statement is explicit and user impact is clear.
- [x] Scope boundaries (in/out) are explicit.
- [x] Acceptance criteria are testable.
- [x] Dependencies and known risks are listed.

# Dependencies and risks
- Les slices encore ouvertes de `req_003` (`task_009` a `task_013`) recouvrent une
  partie de cette requete. Leur promotion devra soit les reutiliser avec une
  tracabilite mise a jour, soit les retirer explicitement ; aucun doublon de task ne
  doit etre cree silencieusement.
- La pagination par curseur modifie le contrat API et l'etat frontend. Une phase de
  compatibilite peut conserver `offset` uniquement pour la premiere page, mais
  l'ordre `(timestamp_s, seq)` est obligatoire des le debut.
- L'ajout du jeton doit rester transparent pour le lancement local et les raccourcis
  Windows/WSL ; le jeton ne doit apparaitre ni dans les logs d'erreur ni dans les
  captures de documentation.
- Les traces reelles et DBC clients restent hors depot. Les tests de performance,
  parsing hostile et export utilisent des fixtures synthetiques reproductibles.
- Le decoupage frontend peut casser les E2E actuels qui lisent les globals. Poser
  `window.__ctd` et migrer les tests avant de rendre les modules prives.
- Le rapport d'import doit reutiliser les donnees deja indexees et ne pas declencher
  un second decodage complet.
- Un theme clair n'est pas exige par cette requete : il peut etre traite ensuite sans
  retarder la clarte fonctionnelle, sous reserve de conserver les tokens CSS. Aucun
  travail de theme clair n'est attendu dans les sept slices.

# Companion docs
- Product brief(s): `prod_002_product_brief_cantracediag_mvp`
- Architecture decision(s): `adr_002_adr_architecture_cantracediag_mvp`

# References
- `README.md`
- `docs/product-brief.md`
- `docs/product-backlog.md`
- `docs/roadmap.md`
- `docs/design-ui.md`
- `docs/audit-complet-2026-07-16.md`
- `logics/request/req_003_robustesse_execution_et_completude_post_audit_2026_07_16.md`
- `src/cantracediag/api.py`
- `src/cantracediag/store.py`
- `src/cantracediag/formats/asc.py`
- `src/cantracediag/web/index.html`
- `src/cantracediag/web/app.js`
- `tests/test_e2e_ui.py`

# AI Context
- Summary: Finaliser le workflow diagnostic et clarifier l'interface CanTraceDiag sur
  la baseline actuelle, puis borner performances, securite et integrite des donnees.
- Keywords: export, rapport import, statistiques curseurs, clarte UI, pagination,
  securite locale, parsing ASC, accessibilite, modularisation
- Use when: Une evolution concerne le workflow diagnostic, sa lisibilite, ses sorties,
  ses performances ou les garanties necessaires a son usage local.
- Skip when: Le changement concerne BLF/MF4, replay, multi-bus, cloud, packaging natif
  ou une fonction deja livree sans regression prouvee.

# Backlog
- `item_017_deliver_diagnostic_report_statistics_and_exports`
- `item_018_bound_hot_endpoints_and_deterministic_trace_navigation`
- `item_019_harden_local_and_lan_api_security`
- `item_020_enforce_asc_parsing_integrity`
- `item_021_improve_accessibility_and_minimal_responsive_support`
- `item_022_modularize_frontend_and_align_dependencies_ci_and_docs`
- `item_023_clarify_final_ui_workflow_in_english`
