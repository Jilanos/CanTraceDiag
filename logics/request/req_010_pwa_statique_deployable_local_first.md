## req_010_pwa_statique_deployable_local_first - PWA statique deployable local-first
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Complexity: Medium
> Theme: General
> Reminder: Update status/understanding/confidence and linked backlog/task references when you edit this doc.

# Needs
- Transformer les jalons 0.1 et 0.2 en une PWA statique local-first déployable :
  une application servie comme fichiers statiques, installable/offline pour le
  shell applicatif, capable de lancer le workflow local trace + DBC sans FastAPI.
- Produire un artefact de build vérifiable et documenter son hébergement derrière
  Caddy, en cohérence avec le modèle `paulmondou.fr`.
- Ajouter les garde-fous utilisateurs attendus pour une PWA locale : gestion des
  workspaces, reprise, purge, export/import portable minimal, quotas stockage et
  messages de récupération.

# Context
- Le jalon 0.1 a validé la lecture ASC chunkée 500 MiB en navigateur.
- Le jalon 0.2 a livré un moteur local fixture-focused : parser ASC, DBC subset,
  decode, store columnar, façade locale et UI minimale sans backend.
- Le jalon 0.3 doit rendre cet ensemble déployable statiquement et opérable
  comme PWA. Il ne doit pas masquer les limites restantes du moteur DBC ni
  prétendre remplacer immédiatement toute l'application FastAPI existante.
- Le modèle de déploiement cible est compatible avec le portail existant :
  fichiers statiques derrière Caddy, sous `paulmondou.fr` ou un sous-domaine.

# Acceptance criteria
- AC1: Un build statique reproductible produit un répertoire distribuable
  contenant HTML, JS, CSS, manifest PWA, service worker et assets nécessaires.
- AC2: L'application fonctionne depuis un serveur statique local sans FastAPI :
  import trace + DBC, status, signaux, trace paginée, série sélectionnée et purge.
- AC3: Le shell PWA est installable/offline : manifest valide, service worker
  enregistré, cache de l'app shell et stratégie claire pour ne pas cacher des
  traces utilisateur par erreur.
- AC4: Une gestion de workspaces locale minimale existe : liste, reprise,
  suppression, purge globale et export/import portable d'un workspace de fixture
  ou format documenté si l'export complet est volontairement différé.
- AC5: Les erreurs de quota/stockage local sont détectées ou simulables et
  présentées avec une voie de récupération compréhensible.
- AC6: La documentation de déploiement statique couvre Caddy et le domaine cible,
  et distingue explicitement la PWA statique de l'architecture FastAPI actuelle.
- AC7: Les validations incluent build statique, tests unitaires navigateur/local,
  smoke Chromium depuis les fichiers buildés et vérification service worker /
  manifest.
- AC8: Les limites restantes avant adoption produit sont documentées : DBC
  complet, performances gros indexes, persistance durable, compatibilité
  navigateurs et stratégie de migration de l'UI principale.

# Definition of Ready (DoR)
- [x] Problem statement is explicit and user impact is clear.
- [x] Scope boundaries (in/out) are explicit.
- [x] Acceptance criteria are testable.
- [x] Dependencies and known risks are listed.

# Companion docs
- Product brief(s): (none yet)
- Architecture decision(s): (none yet)
- Roadmap(s): `road_001_architecture_pwa_spa_local_first`

# References
- `logics/roadmap/road_001_architecture_pwa_spa_local_first.md`
- `spikes/pwa-500mb/results-2026-07-22.md`
- `spikes/pwa-local-engine/results-2026-07-22.md`
- `spikes/pwa-local-engine/storage-decision-2026-07-22.md`
- `/home/paul/dev/Kapsule/deploy/Caddyfile`
- `/home/paul/dev/Kapsule/deploy/README.md`

# AI Context
- Summary: Request for roadmap milestone 0.3: package the browser-local
  ASC/DBC engine as a static installable PWA with service worker, workspace
  lifecycle, static hosting documentation, quota recovery and smoke validation.
- Keywords: request-draft, pwa, spa, static build, service worker, manifest,
  caddy, local-first, workspace, quota, offline, deployment
- Use when: Starting or reviewing the static deployable PWA milestone.
- Skip when: Implementing deeper ASC/DBC engine parity or the existing FastAPI
  backend workflow.

# Backlog
- `item_020_pwa_statique_deployable_local_first`
