# Audit bout en bout CanTraceDiag

Date : 15 juillet 2026  
Périmètre : produit, parcours fonctionnels, UI, design, accessibilité, architecture,
qualité logicielle, sécurité locale et performance.  
Version auditée : `d71bbad` (`main`, synchronisée avec `origin/main`).

## 1. Synthèse exécutive

CanTraceDiag est un MVP fonctionnel et cohérent pour une utilisation locale sur grand
écran. La chaîne ASC -> DBC -> décodage -> DuckDB -> API -> graphes et vue trace est
réelle, testée et utilisable. Les curseurs A/B, la synchronisation graphe/trace, le
downsampling serveur, les filtres principaux et la résolution visuelle des conflits
DBC donnent déjà une base nettement supérieure à une simple preuve de concept.

Le projet n'est toutefois pas encore suffisamment fiable pour prendre des décisions de
diagnostic sans garde-fous. Le principal risque est la sélection silencieuse d'une DBC
quand plusieurs versions décrivent le même ID avec le même nom de message. Les données
réelles contiennent précisément ce cas, avec des définitions différentes. Deux autres
points doivent être corrigés avant une diffusion plus large : l'injection HTML possible
depuis une trace importée et une CI qui n'installe pas les dépendances API nécessaires à
la suite de tests.

L'objectif produit de 40 à 150 Mo est atteint en temps d'import sans DBC, mais pas avec
une marge mémoire confortable. Une trace de 44 Mo et les 14 DBC réelles consomment près
de 850 Mo au pic. Le stockage DuckDB reste en mémoire, sans cache persistant, ce qui
limite fortement l'extrapolation vers 150 Mo décodés.

Évaluation synthétique :

| Axe | État | Appréciation |
|---|---|---|
| Fonctionnel | Bon MVP, critères P0 encore partiels | 7/10 |
| Justesse diagnostic | Risque DBC silencieux bloquant | 4/10 |
| UI desktop | Dense, lisible, adaptée au métier | 7/10 |
| Responsive | Cassé à 1280 px et inutilisable sur mobile | 2/10 |
| Accessibilité | Souris dominante, canvas non nommé | 4/10 |
| Performance interactive | Bonne sur 2,58 M d'échantillons | 8/10 |
| Scalabilité import | Temps correct, mémoire trop élevée | 5/10 |
| Qualité automatisée | 50 tests et lint OK, CI mal configurée | 7/10 |

Verdict : **MVP exploitable en interne sur desktop, avec correctifs P0 obligatoires avant
d'en faire un outil de diagnostic de confiance.**

## 2. Méthode et preuves

L'audit a combiné :

- lecture du brief, du backlog, de la roadmap, des ADR et du code complet ;
- exécution de `pytest` et `ruff` dans l'environnement virtuel du projet ;
- lancement de l'application FastAPI et inspection Playwright en 1600x900, 1280x720 et
  390x844 ;
- vérification de l'arbre d'accessibilité Chromium ;
- import chronométré des deux traces réelles locales, conservées hors dépôt ;
- import de la trace de 44 Mo avec les 14 DBC réelles et mesure des requêtes usuelles ;
- contrôle du workflow avec `logics-manager status`, `health`, `audit` et `lint`.

Les mesures de performance sont des mesures locales ponctuelles, pas des SLA. Elles
servent à établir les ordres de grandeur et les points de saturation.

## 3. Architecture observée

Le projet suit une architecture locale simple :

```text
ASC + DBC
   -> parser ASC en flux
   -> décodage cantools
   -> lots Python / pandas
   -> DuckDB en mémoire
   -> API FastAPI à session unique
   -> UI HTML/CSS/JavaScript + canvas
```

Points solides :

- séparation claire entre parsing, catalogue DBC, décodage, pipeline, stockage et API ;
- modèle normalisé conservant les trames brutes et les événements non-data ;
- ingestion par lots de 50 000 éléments, sans lecture eager de toute la trace ;
- requêtes API bornées, pagination de la trace et downsampling min/max ;
- sérialisation explicite de l'accès à la connexion DuckDB partagée ;
- application locale sans dépendance cloud ni envoi des traces vers un tiers.

Écarts entre architecture annoncée et architecture réelle :

- aucun cache Parquet ou DuckDB persistant n'est produit ;
- la base est `:memory:` par défaut et disparaît à chaque redémarrage ;
- `pyarrow` et `python-can` sont déclarés mais ne participent pas au chemin principal ;
- l'API et l'UI partagent une session globale unique, adaptée au MVP monoposte mais non
  isolée contre des imports ou requêtes concurrentes ;
- le frontend est un fichier JavaScript de plus de 1 000 lignes sans découpage en
  modules ni outillage de lint dédié.

## 4. Couverture fonctionnelle

| Capacité attendue | État observé | Conclusion |
|---|---|---|
| Import ASC par chemin ou navigateur | Implémenté, lecture en flux | Conforme MVP |
| Événements `ErrorFrame` / `Status` | Conservés et filtrables | Conforme |
| Plusieurs DBC | Chargement et catalogue implémentés | Conforme partiel |
| Résolution des IDs DBC en conflit | Popup par ID si les noms diffèrent | Non fiable dans tous les cas |
| Décodage physique | `cantools`, unités, valeurs numériques/texte | Conforme partiel |
| Graphes empilés | Canvas, sample-and-hold, axe commun | Conforme |
| Zoom/pan/fit | Implémenté et testé E2E | Conforme |
| Curseurs A/B et deltas | Implémentés sans interpolation | Conforme |
| Synchronisation graphe/trace | Bidirectionnelle | Conforme |
| Vue trace paginée | Frames + événements, 200 lignes/page | Conforme |
| Filtres trace | Temps, ID, message, direction, statut, événement | Signal absent |
| Colonnes configurables | Visibilité, ordre, largeur minimale, temps | Formats ID/data absents |
| Recherche de signaux | Nom message + signal | ID, unité et DBC absents |
| Préférences locales | Sélections, favoris, layout, colonnes, filtres principaux | Temps non persisté |
| Exports CSV/Parquet | Non implémentés | P1/P2 annoncé |
| BLF/MF4, multi-bus, replay | Non implémentés | Hors périmètre assumé |

## 5. Constats prioritaires

### P0 - Justesse, sécurité et intégration

#### F-01 - Les conflits DBC de même nom sont ignorés

`DbcCatalog.find_ambiguous_ids()` ne considère un ID ambigu que si plusieurs entrées ont
des noms de message différents. Le décodeur prend sinon la première entrée, donc l'ordre
des fichiers détermine silencieusement la définition utilisée.

Preuve sur les 14 DBC réelles : les IDs `0x720` à `0x725` et `0x710` existent dans trois
versions `DebugBCM`. Pour `0x723`, une version contient trois signaux et deux versions en
contiennent quatre. Aucun de ces IDs n'est proposé dans la popup de résolution.

Impact : une valeur peut être absente ou décodée selon une définition non choisie par
l'opérateur. Dans un outil de diagnostic, ce risque invalide la confiance dans le
résultat.

Correction attendue : considérer tout doublon d'ID comme conflit sauf équivalence
structurelle prouvée par une empreinte canonique ; exiger une résolution valide et
persistante par ID ; identifier une DBC par un identifiant stable, pas seulement son nom
de fichier ; afficher la décision dans le rapport d'import.

Références : `src/cantracediag/dbc.py:81`, `src/cantracediag/decode.py:75`.

#### S-01 - Les données importées peuvent injecter du HTML dans l'UI locale

La table et l'inspecteur assemblent avec `innerHTML` des champs issus de l'API. Le détail
d'un événement ASC inconnu est conservé tel quel par le parser puis rendu sans
échappement. Les noms, unités et valeurs DBC suivent aussi plusieurs chemins
`innerHTML`.

Impact : une trace ou une DBC préparée peut exécuter du JavaScript dans l'origine locale
de CanTraceDiag. Le caractère local réduit l'exposition réseau, mais pas le risque lié à
un fichier d'acquisition externe.

Correction attendue : construire les cellules avec `textContent`/DOM, centraliser un
échappement strict pour les rares fragments HTML statiques, ajouter une Content Security
Policy et un test E2E avec charge utile hostile.

Références : `src/cantracediag/web/app.js:705`, `src/cantracediag/web/app.js:747`,
`src/cantracediag/web/app.js:781`.

#### Q-01 - La CI n'installe pas l'extra API

Le workflow installe `.[dev]`, alors que les tests importent FastAPI/Starlette et que ces
dépendances ne sont déclarées que dans l'extra `api`. Le README donne la commande
correcte `.[dev,api]`.

Impact : un runner propre ne dispose pas contractuellement des dépendances nécessaires ;
la CI n'est pas reproductible telle qu'elle est décrite.

Correction attendue : installer `.[dev,api]`, ajouter une matrice sur les versions Python
supportées utiles et conserver un test d'installation du paquet.

Références : `.github/workflows/ci.yml:14`, `pyproject.toml:23`.

### P1 - Robustesse, performance et utilisabilité

#### P-01 - Le pic mémoire limite les grosses traces décodées

Mesures d'import :

| Trace | DBC | Résultat | Temps mur | Pic RSS |
|---|---|---:|---:|---:|
| 44 Mo | aucune | 400 612 frames, 414 événements | 8,21 s | 396 Mo |
| 155 Mo | aucune | 1 238 781 frames, 117 088 événements | 24,45 s | 630 Mo |
| 44 Mo | 14 DBC | 361 689 frames décodées, 2 584 851 samples | 24,39 s | 850 Mo |

L'ingestion est bornée par lots, mais chaque lot devient une liste de dictionnaires puis
un DataFrame, tandis que toutes les tables DuckDB restent en RAM. La trace décodée de
155 Mo risque donc de dépasser plusieurs gigaoctets selon le nombre de signaux.

Correction attendue : base temporaire persistante hors dépôt, transactions et insertions
Arrow/DuckDB plus directes, cache adressé par empreinte trace+DBC+résolutions, nettoyage
géré, budget mémoire mesuré et test de non-régression sur données synthétiques.

Références : `src/cantracediag/store.py:63`, `src/cantracediag/store.py:95`,
`src/cantracediag/pipeline.py:16`.

#### P-02 - L'indexation bloque la requête d'upload et n'a pas de progression réelle

`/api/import-files` est asynchrone pour l'upload mais appelle ensuite le pipeline CPU de
façon synchrone dans la coroutine. L'UI passe de la progression réseau à un libellé
`Indexing...` sans pourcentage, phase, estimation, annulation ni récupération détaillée
d'erreur.

Correction attendue : job d'import explicite avec état serveur, progression par bytes,
frames et phases, polling ou SSE, annulation propre et conservation de la session
précédente jusqu'au succès du nouvel import.

Références : `src/cantracediag/api.py:177`, `src/cantracediag/web/app.js:104`.

#### U-01 - Le layout n'est pas responsive

Mesures Playwright :

| Viewport | Largeur du contenu | Effet |
|---|---:|---|
| 1600 px | 1600 px | Correct |
| 1280 px | 1447 px | Boutons `Columns`, `Next` et inspecteur hors écran |
| 390 px | 1447 px | Centre et presque toutes les actions hors écran |

Les panneaux latéraux ont des largeurs fixes et la zone centrale conserve environ
1 075 px. Le `body` masque le débordement, ce qui rend les contrôles inaccessibles plutôt
que simplement scrollables.

Correction attendue : desktop compact dès 1280 px, repli automatique des panneaux à des
breakpoints déterministes, barre d'outils adaptable, mode étroit avec tiroirs/onglets et
tests E2E 1280/1024/390 sans contrôle hors viewport.

Références : `src/cantracediag/web/index.html:51`,
`src/cantracediag/web/index.html:55`, `src/cantracediag/web/index.html:85`.

#### F-02 - Les filtres et formats P0 de la vue trace sont incomplets

Le backlog demande un filtre par signal et des formats hexadécimal, décimal et binaire
lorsque pertinents. L'API ne filtre pas les frames par présence/valeur de signal et la
configuration de colonne ne propose un format que pour le timestamp. La largeur saisie
est appliquée comme `min-width`, pas comme largeur maîtrisée.

Correction attendue : filtre signal côté serveur, formats ID/DLC/data documentés, largeur
réellement redimensionnable et tests de combinaison/persistance.

Références : `src/cantracediag/store.py:314`,
`src/cantracediag/web/app.js:789`.

#### F-03 - La recherche de signaux ne couvre pas les métadonnées annoncées

Le filtre client ne cherche que `message.signal`. Il ne couvre ni ID CAN, ni unité, ni
nom de DBC. Tous les signaux de toutes les DBC sont listés, y compris ceux absents de la
trace ou appartenant à une DBC écartée lors d'une résolution.

Correction attendue : index de recherche sur message, signal, ID, unité et DBC ; facettes
`présent dans la trace` et `DBC retenue` ; compte d'occurrences et état vide explicite.

Référence : `src/cantracediag/web/app.js:203`.

#### R-01 - Les erreurs d'import et résolutions invalides sont insuffisamment contrôlées

Les erreurs de parsing DBC remontent en erreur 500 générique. `/api/resolve` accepte une
résolution incomplète ou un nom de DBC inexistant, puis le décodeur retombe silencieusement
sur la première entrée. Deux DBC portant le même basename peuvent aussi s'écraser dans le
dossier temporaire. Enfin, le décodage autorise les payloads tronqués et peut marquer une
frame partiellement décodée comme `ok`.

Correction attendue : validation de schéma métier, erreurs 4xx actionnables, résolution
exhaustive et vérifiée, noms temporaires uniques, politique explicite sur DLC/payload et
statuts `truncated`/`decode_error` auditables.

Références : `src/cantracediag/api.py:193`, `src/cantracediag/api.py:222`,
`src/cantracediag/decode.py:53`.

#### A-01 - L'accessibilité clavier et lecteur d'écran est faible

L'arbre Chromium expose un canvas sans nom. Les boutons de repli sont nommés `‹`/`›`, les
boutons de zoom `+`/`-`, le favori est un `span` cliquable et l'ordre des colonnes repose
sur le drag-and-drop. Le canvas n'est ni focusable ni pilotable au clavier.

Correction attendue : noms accessibles, focus visible, commandes clavier pour curseurs
et navigation, bouton favori réel, alternative tabulaire/résumé au canvas, réordonnancement
par boutons et vérification automatisée minimale axe-core.

Références : `src/cantracediag/web/index.html:159`,
`src/cantracediag/web/app.js:236`, `src/cantracediag/web/app.js:789`.

#### T-01 - Les tests ne couvrent pas les risques nouvellement identifiés

La suite actuelle passe : **50 tests**, avec un avertissement de dépréciation Starlette.
`ruff` passe également. Les tests E2E protègent bien les régressions récentes de curseur,
repli de panneaux et concurrence DuckDB, mais uniquement sur viewport 1600 px.

Manquent notamment : collisions DBC de même nom, XSS, import DBC invalide, résolution
incomplète, payload tronqué, responsive, clavier/accessibilité, formats de colonnes,
recherche avancée, filtre signal, progression/annulation et budget mémoire.

### P2 - Cohérence produit et maintenabilité

#### D-01 - L'UI est efficace mais trop dense pour une première prise en main

Le design sombre, la palette sémantique, les graphes empilés et la table compacte sont
adaptés au métier. L'information importante est visible sans cartes décoratives et les
états `ok`, warning et erreur sont distingués.

En revanche, l'en-tête mélange import, fichiers, résumé et progression ; la barre graphe
combine commandes et mode d'emploi permanent ; la barre trace contient neuf filtres et
la pagination sur deux lignes dès 1600 px. Les tailles 11-13 px et les noms tronqués de
signaux demandent de l'attention prolongée. L'état vide dit seulement de sélectionner des
signaux, sans clarifier la séquence trace -> DBC -> chargement -> sélection.

Correction attendue : hiérarchie en trois niveaux (import/statut, analyse, inspection),
filtres secondaires dans un panneau compact, info-bulles contextuelles, états vides
orientés action et affichage complet du signal au survol/focus.

#### D-02 - Documentation et dépendances dérivent de l'implémentation

Le README annonce Parquet/DuckDB et une table virtualisée, alors que le stockage est en
mémoire et la table paginée. La roadmap présente encore comme futures plusieurs fonctions
déjà livrées. Les dépendances ont seulement des bornes minimales et aucun lock de
développement, ce qui réduit la reproductibilité.

Correction attendue : mettre à jour README/roadmap/ADR, distinguer cible et état courant,
retirer ou justifier les dépendances inutilisées et adopter une stratégie de verrouillage
ou de contraintes testées.

## 6. Performance interactive

Sur la trace de 44 Mo décodée en 2,58 millions d'échantillons, les requêtes répétées à
chaud donnent :

| Opération | Latence observée |
|---|---:|
| Série complète downsamplée | 23-25 ms |
| Série sur fenêtre de 10 s | 9-10 ms |
| Échantillon le plus proche | 8-11 ms |
| Page trace à offset 100 000 | 46-60 ms |
| Page trace filtrée par ID | 28-31 ms |
| Localisation temporelle trace | 15-17 ms |

Ces résultats sont bons pour le MVP. Le verrou global DuckDB sérialise toutefois les
requêtes envoyées en parallèle par l'UI : avec beaucoup de signaux et deux curseurs, la
latence cumulée peut devenir visible. La priorité reste le stockage disque et la mémoire ;
les index ou connexions de lecture multiples ne doivent être ajoutés qu'après profiling
sur la base persistante cible.

## 7. Plan de correction recommandé

### Lot 1 - Confiance diagnostic et sécurité

- Corriger la détection/résolution de tous les doublons DBC.
- Valider les résolutions et rendre leur résultat reproductible.
- Supprimer les injections `innerHTML` de données importées et ajouter une CSP.
- Corriger l'installation CI et ajouter les tests P0.

Sortie : aucune sélection DBC silencieuse, aucune exécution HTML depuis un fichier, CI
propre reproductible.

### Lot 2 - Import robuste et scalable

- Déporter l'index DuckDB sur disque temporaire/cache.
- Réduire les conversions Python/pandas et instrumenter temps/mémoire.
- Introduire un job d'import progressif, annulable et transactionnel.
- Garder l'analyse précédente active jusqu'au succès du nouvel import.

Sortie : trace 150 Mo décodée sous budget mémoire défini, progression exploitable.

### Lot 3 - Complétude du workflow diagnostic

- Ajouter filtre signal, recherche multi-métadonnées et rapport d'import.
- Finaliser les formats et largeurs de colonnes.
- Masquer ou marquer les signaux absents/non retenus.
- Ajouter les exports CSV ciblés si confirmés par l'utilisateur.

Sortie : critères PB-005/PB-006 réellement couverts de bout en bout.

### Lot 4 - Responsive, accessibilité et finition design

- Recomposer le layout à 1280/1024 px et fournir un mode étroit cohérent.
- Rendre les interactions critiques accessibles au clavier.
- Simplifier les barres d'outils et améliorer les états vides/erreurs.
- Ajouter les tests visuels, responsive et accessibilité.

Sortie : aucun contrôle hors viewport, parcours principal clavier possible, UI cohérente
sur les largeurs supportées.

### Lot 5 - Documentation et maintenabilité

- Synchroniser documentation, dépendances et architecture réelle.
- Découper progressivement le frontend par responsabilités, sans réécriture de framework.
- Ajouter lint/format JS et budgets de performance dans la CI.

## 8. Critères de sortie globaux

Le durcissement peut être considéré terminé quand :

- toute collision DBC est soit prouvée équivalente, soit explicitement résolue ;
- une trace/DBC hostile ne peut injecter ni HTML ni script ;
- la CI repart d'un environnement propre et exécute lint, tests API et E2E critiques ;
- une trace réelle de 150 Mo avec DBC respecte un budget documenté de temps et mémoire ;
- l'import expose phase, progression, erreur actionnable et annulation ;
- les recherches/filtres/formats du backlog P0 sont couverts par tests ;
- aucun contrôle principal ne sort des viewports supportés ;
- les actions principales sont nommées et pilotables au clavier ;
- README, roadmap et ADR décrivent sans ambiguïté l'état livré et la cible suivante.

## 9. Validation exécutée

- `.venv/bin/pytest -q` : 50 tests passés, 1 avertissement de dépréciation.
- `.venv/bin/ruff check .` : succès.
- `logics-manager health` : aucun signal d'incident.
- `logics-manager audit --group-by-doc` : succès avant création de la présente requête.
- `logics-manager lint --require-status` : succès avant création de la présente requête.
- Playwright : aucun crash JavaScript/API sur le parcours inspecté ; défauts responsive et
  accessibilité détaillés ci-dessus.

## 10. Requête de remédiation

La demande associée est
`logics/request/req_002_fiabiliser_cantracediag_apres_audit_fonctionnel_ui_et_performance.md`.
Elle transforme les constats de ce rapport en critères d'acceptation testables et en lots
de livraison ordonnés.
