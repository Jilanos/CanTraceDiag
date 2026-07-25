# Audit technique - CanTraceDiag

Date : 2026-07-25  
Revision auditee : `acb404a` (`main`)  
Perimetre : code Python, frontend historique, PWA locale, tests, CI/CD, conteneur et gouvernance Logics.

## Verdict

Le socle Python est mature pour un projet de cette taille : le lint est propre, 155 tests passent
et les controles de securite locaux sont bien couverts. Le risque principal n'est plus le moteur
CAN, mais la coexistence de deux produits et de deux chemins de livraison :

- l'application FastAPI documentee et testee en continu ;
- la PWA statique construite depuis `spikes/pwa-local-engine/`, qui est l'artefact Docker deploye.

Cette divergence rend possible une release verte cote Python mais cassee ou fonctionnellement
incomplete cote PWA.

## Verifications executees

| Controle | Resultat |
| --- | --- |
| `.venv/bin/ruff check .` | OK |
| `.venv/bin/pytest -q` | 155 tests passes, 1 avertissement deprecation Starlette |
| Tests Node PWA | Non executes localement : Node 20.20.2, fonctionnalites Node 22 requises |
| Build PWA local | Meme incompatibilite Node 20 ; le Dockerfile et la release utilisent Node 22 |
| `logics-manager health` | 96 documents, aucun signal structurel |
| `logics-manager lint` | OK |
| `logics-manager audit` | Echec : 47 blocages et 17 avertissements de tracabilite |

## Constats prioritaires

### P0 - La PWA n'est pas validee sur les pull requests

Le workflow `ci.yml` ne teste que Python/FastAPI. Les tests TypeScript et le build navigateur sont
dans `release.yml`, donc executes uniquement apres creation d'un tag `v*`. Une regression PWA peut
ainsi atteindre `main` sans controle et n'etre detectee qu'au debut d'une release.

Solution :

1. Ajouter un job `pwa` a `ci.yml` avec Node 22.
2. Executer les tests `spikes/pwa-local-engine/tests/*.test.ts`.
3. Construire le site puis verifier que tous les fichiers de `APP_SHELL` existent.
4. Ajouter au minimum un smoke test navigateur sur le site genere.

### P0 - Deux architectures produit sont maintenues en parallele

Le README et la CI principale decrivent l'application FastAPI/DuckDB, alors que le Dockerfile
publie exclusivement la PWA statique. Le repertoire de production porte encore le nom `spikes/`.
Les garanties ne sont pas equivalentes : stockage, export, performances, securite et limites de
taille divergent entre les deux moteurs.

Solution :

- prendre une decision explicite sur l'artefact canonique ;
- si la PWA est la cible, sortir son code de `spikes/` vers un package/application de premier rang ;
- publier une matrice de parite fonctionnelle et de limites entre FastAPI et PWA ;
- separer clairement dans le README les modes "desktop local" et "PWA hebergee".

### P1 - Le build PWA repose sur des remplacements textuels fragiles

`build-browser.mjs` concatene huit fichiers JavaScript puis remplace des blocs grace a des marqueurs
de texte. Un changement de commentaire, d'indentation ou de signature dans le frontend historique
peut casser le build ou, plus grave, produire un remplacement partiel difficile a relire.

Solution :

- extraire une couche UI independante du transport ;
- injecter une implementation `ApiClient` FastAPI ou locale au lieu de reecrire le code source ;
- utiliser un vrai compilateur/bundler TypeScript avec imports explicites ;
- conserver temporairement des assertions fortes sur chaque remplacement et un test du bundle.

### P1 - La gouvernance Logics n'est pas au niveau du code

`logics-manager audit` remonte 47 blocages, surtout des criteres d'acceptation sans preuve au niveau
des taches. Deux taches sont encore ouvertes et deux demandes restent en brouillon alors que des
commits de livraison PWA sont deja presents. L'historique de decision ne permet donc pas de
reconstituer proprement ce qui est fini, reporte ou remplace.

Solution :

- clore ou requalifier les workflows historiques ;
- rattacher chaque critere d'acceptation a une preuve (test, commit, capture ou document) ;
- supprimer les doublons de demandes PWA ou les marquer explicitement comme remplaces ;
- rendre `logics-manager audit` bloquant avant une release, une fois la dette historique resorbee.

### P1 - Les en-tetes de securite HTTP sont absents

`nginx.conf` ne configure ni CSP, ni `X-Content-Type-Options`, ni politique de referent, ni
protection d'encapsulation. Pour une PWA traitant potentiellement des donnees vehicule sensibles,
la defense en profondeur du frontend heberge doit etre explicite.

Solution :

- ajouter une CSP compatible avec les modules utilises ;
- ajouter `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer`,
  `Permissions-Policy` restrictive et `frame-ancestors 'none'` via CSP ;
- tester les en-tetes dans le smoke test de l'image.

### P2 - Reproductibilite et supply chain perfectibles

Les images `node:22-bookworm-slim` et `nginxinc/nginx-unprivileged:1.27-alpine` sont des tags
mutables. Les actions GitHub sont versionnees par tags majeurs. Aucun SBOM, scan d'image ou
attestation de provenance n'est publie.

Solution :

- pinner les images par digest et automatiser leur renouvellement ;
- pinner les actions par SHA ;
- generer un SBOM, scanner l'image et produire une attestation de provenance ;
- ajouter des labels OCI avec revision et source.

### P2 - Prerequis Node incompletement documente

Le build utilise `stripTypeScriptTypes`, indisponible avec le Node 20 installe localement. Le README
annonce seulement Python 3.11+ pour le developpement principal.

Solution : ajouter `.nvmrc` ou `.tool-versions`, declarer Node >= 22, et fournir une commande unique
de validation PWA.

### P2 - Dette de maintenabilite encore concentree

`api.py` et `store.py` depassent chacun 1 100 lignes. La couverture limite le risque immediat, mais
les responsabilites API, cycle de session, import, export et requetes analytiques restent fortement
couplees. L'avertissement Starlette/httpx annonce aussi une migration de test a anticiper.

Solution : decomposer par domaine lors des prochaines evolutions, sans refonte globale, et traiter
la deprecation Starlette avant qu'elle ne devienne une incompatibilite.

## Plan recommande

### Dans les 48 heures

- Faire tourner build et tests PWA sur chaque PR avec Node 22.
- Ajouter un smoke test du site genere et des en-tetes Nginx.
- Clarifier dans le README quel artefact est deploye en production.

### Dans les deux prochaines iterations

- Transformer la PWA de `spike` en application de premier rang.
- Remplacer les transformations textuelles par une interface de transport.
- Resorber les blocages Logics lies aux workflows actifs et aux releases recentes.

### Ensuite

- Pinner la supply chain, produire SBOM et provenance.
- Decomposer progressivement `api.py` et `store.py`.
- Etablir des budgets de performance et de taille sur des traces realistes pour la PWA.

## Points forts a conserver

- Suite de tests Python et securite substantielle.
- Donnees de test synthetiques et approche local-first coherente.
- Build Docker multi-stage et execution Nginx non privilegiee.
- Documentation d'architecture et preuves de migration deja riches.
