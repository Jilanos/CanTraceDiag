## req_004_optimiser_le_chargement_des_grosses_traces_par_decodage_a_la_demande - Optimiser le chargement des grosses traces par décodage à la demande
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: Réduire fortement le temps de chargement des traces ASC volumineuses en évitant de décoder et stocker tous les signaux au moment de l'import ; indexer d'abord les trames brutes puis décoder uniquement les signaux consultés.
> Confidence: high
> Complexity: high
> Theme: performance
> Reminder: Update status/understanding/confidence and linked backlog/task references when you edit this doc.

# Needs
- Réduire le temps de chargement initial des traces ASC volumineuses (>100 Mo) en
  supprimant le décodage exhaustif de tous les signaux pendant l'import.
- Conserver un import utile immédiatement : indexer les trames brutes, événements,
  timestamps, IDs, payloads, direction, statut de décodabilité et nom de message quand
  il est déterminable sans matérialiser tous les samples.
- Décoder les signaux à la demande, uniquement lorsqu'un opérateur les sélectionne
  dans l'UI ou lorsqu'une fonction en a besoin (courbe, curseur, détail de trame,
  filtre signal).
- Mettre en cache les séries décodées déjà demandées afin que zoom, curseurs et
  rechargements de la même sélection ne redécodent pas inutilement.
- Maintenir l'exactitude diagnostic : aucune interpolation, valeurs physiques
  identiques au décodage actuel, gestion inchangée des IDs inconnus, erreurs de
  décodage et conflits DBC.
- Rendre la performance observable par des mesures automatiques : temps d'import,
  temps de première série, nombre de trames lues, nombre de trames décodées et nombre
  de samples matérialisés.

# Context
- Le pipeline actuel lit la trace puis appelle `Decoder.decode_frame()` pour chaque
  trame dans `src/cantracediag/pipeline.py`. Quand un DBC est chargé, ce chemin appelle
  `cantools.message.decode(...)` et crée un `DecodedSignalSample` pour chaque signal du
  message, même si l'utilisateur n'affichera ensuite que 2 à 8 signaux.
- `TraceStore` stocke aujourd'hui toutes les valeurs décodées dans la table `samples`.
  Les endpoints `/api/series`, `/api/cursor`, `/api/frame-signals`, le filtre trace par
  signal et `/api/signals` supposent donc que les samples existent déjà.
- Sur les fichiers >100 Mo, l'expérience opérateur est dégradée : le chargement initial
  attend un travail de décodage et d'insertion qui ne correspond pas au besoin réel de
  visualisation immédiate.
- La liste des signaux peut venir du DBC sans pré-décoder toute la trace. La présence
  effective d'un signal peut être déterminée plus tard, à partir des IDs présents dans
  les trames ou du cache de séries décodées.
- Le gain attendu est important mais dépend du DBC : objectif produit pragmatique,
  diviser au minimum par 3 le temps de chargement initial sur une trace synthétique
  volumineuse avec DBC riche, sans dégrader les résultats affichés.

# Product decisions
- Le chargement initial devient un import brut indexé : il doit privilégier la mise à
  disposition rapide de la trace et de la table, pas la pré-matérialisation de tous les
  signaux.
- Le décodage à la demande se fait par clé signal `(message_name, signal_name)` et par
  plage temporelle quand c'est possible, en ne parcourant que les trames portant
  l'arbitration ID du message concerné.
- Le cache de séries décodées est local à la session courante. Il peut vivre dans
  DuckDB ou dans une table dédiée, mais doit rester invalidé proprement à chaque nouvel
  import, résolution DBC ou changement de DBC.
- Les fonctions de détail ponctuel (`/api/cursor`, `/api/frame-signals`) peuvent
  décoder une fenêtre ou une trame isolée si la série complète n'est pas encore en
  cache.
- Le comportement visible doit rester compatible avec l'UI actuelle : cocher un signal
  déclenche le chargement de sa courbe ; les zooms et curseurs restent bornés ; les
  erreurs sont visibles et n'incohérent pas les checkboxes.
- La requête ne demande pas de support BLF/MF4, de cache persistant entre redémarrages
  serveur, ni de moteur de décodage autre que `cantools`.

# Acceptance criteria
- AC1: L'import initial d'une trace avec DBC ne matérialise plus tous les signaux dans
  `samples` par défaut ; un test vérifie qu'une trace multi-signaux peut être chargée
  avec zéro ou un nombre borné de samples décodés avant toute sélection utilisateur.
- AC2: L'import conserve les informations nécessaires à la navigation : résumé,
  bornes temporelles, pagination trace, événements, IDs, statut de décodabilité,
  noms de messages connus et conflits DBC restent disponibles après chargement.
- AC3: `/api/signals` liste les signaux du DBC sans dépendre de la pré-existence de
  tous les samples ; l'indicateur de présence est soit dérivé des IDs présents, soit
  explicitement marqué comme non encore calculé.
- AC4: `/api/series` décode uniquement le signal demandé, sur la plage demandée quand
  elle est fournie, et retourne les mêmes valeurs que l'ancien import exhaustif pour
  les fixtures existants.
- AC5: Une série déjà demandée est réutilisée depuis un cache local de session pour les
  requêtes compatibles ; un test vérifie qu'un second appel identique ne redécode pas
  les mêmes trames.
- AC6: `/api/cursor` et `/api/frame-signals` fonctionnent même si la série n'a pas été
  pré-décodée ; ils décodent le minimum nécessaire et gardent l'absence
  d'interpolation.
- AC7: Le filtre de trace par signal reste disponible ou affiche explicitement qu'il
  déclenche un décodage ciblé ; il ne force jamais le décodage global de toute la trace.
- AC8: Les erreurs de décodage, IDs inconnus, trames remote, IDs ambigus et résolutions
  DBC gardent le même sens fonctionnel qu'avant la modification.
- AC9: Un benchmark synthétique reproductible couvre au moins deux scénarios : import
  brut sans sélection et première demande de 1 à 8 signaux. Il publie temps d'import,
  temps de décodage à la demande, trames parcourues, samples créés et taille du cache.
- AC10: Sur le benchmark de référence avec DBC riche, le temps d'import initial est au
  moins 3 fois plus rapide que le comportement exhaustif de référence, ou l'écart est
  documenté avec une cause mesurée.
- AC11: La mémoire reste bornée pendant l'import et pendant le décodage à la demande ;
  aucun batch ne matérialise toute la trace ni tous les samples de tous les signaux en
  RAM.
- AC12: Les tests existants de pipeline, store, API et E2E restent verts après
  adaptation des attentes liées au décodage paresseux.

# Suggested implementation slices
- Slice 1: Séparer l'index brut de la matérialisation des samples : stocker les trames
  avec assez de métadonnées DBC pour retrouver rapidement le message et ses signaux.
- Slice 2: Ajouter un service de décodage ciblé par signal/plage, avec cache de séries
  et invalidation par session.
- Slice 3: Adapter `/api/signals`, `/api/series`, `/api/cursor`, `/api/frame-signals`
  et le filtre trace par signal au modèle paresseux.
- Slice 4: Ajouter les tests de non-régression de valeurs et les mesures de performance
  synthétiques.
- Slice 5: Ajuster l'UI pour rendre visibles les états "série en cours de décodage",
  erreur ciblée et présence non encore calculée si nécessaire.

# Out of scope
- Support de nouveaux formats de trace (BLF, MF4, MDF).
- Cache durable réutilisable après redémarrage du serveur.
- Réécriture du frontend ou remplacement de DuckDB.
- Décodage parallèle multi-processus, sauf si nécessaire pour atteindre le budget de
  performance après mesure.
- Export CSV/Parquet, statistiques entre curseurs et sécurité locale, déjà couverts
  par d'autres requêtes.

# Definition of Ready (DoR)
- [x] Problem statement is explicit and user impact is clear.
- [x] Scope boundaries (in/out) are explicit.
- [x] Acceptance criteria are testable.
- [x] Dependencies and known risks are listed.

# Dependencies and risks
- Le changement touche `pipeline.py`, `decode.py`, `store.py`, `api.py` et `app.js` :
  il modifie un contrat central du produit, pas seulement une optimisation locale.
- Les requêtes existantes sur `samples` doivent être adaptées sans perdre les garanties
  de décimation, curseur sans interpolation et pagination bornée.
- `cantools` décode naturellement un message complet ; extraire un seul signal peut
  nécessiter soit de filtrer le résultat décodé, soit d'utiliser les primitives de
  signaux avec prudence. La priorité est de limiter les trames décodées, puis les
  samples stockés.
- Le cache doit être invalidé lors d'un nouvel import, d'une résolution DBC ou d'un
  changement de catalog DBC pour éviter des courbes incohérentes.
- Les benchmarks doivent éviter les fixtures minuscules : utiliser une trace
  synthétique assez large pour révéler le coût réel sans rendre la CI instable.

# Companion docs
- Product brief(s): (none yet)
- Architecture decision(s): (none yet)

# References
- `src/cantracediag/pipeline.py`
- `src/cantracediag/decode.py`
- `src/cantracediag/store.py`
- `src/cantracediag/api.py`
- `src/cantracediag/web/app.js`
- `tests/test_store_pipeline.py`
- `tests/test_api.py`
- `tests/test_diagnostic.py`
- `logics/request/req_003_robustesse_execution_et_completude_post_audit_2026_07_16.md`

# AI Context
- Summary: Optimize large ASC trace loading by replacing exhaustive import-time signal
  decoding with raw-frame indexing, targeted on-demand decoding, and per-session series
  caching.
- Keywords: cantracediag, performance, lazy-decode, on-demand-decoding, large-traces,
  cantools, duckdb, signal-cache, import-time
- Use when: Planning or implementing lazy signal decoding, reducing import latency for
  large traces, or adapting APIs that currently assume precomputed samples.
- Skip when: Work targets export, local API security, BLF/MF4 support, frontend
  framework migration, or persistent analysis reopening.

# Backlog
- none
- `item_014_optimiser_le_chargement_des_grosses_traces_par_decodage_a_la_demande`
