## item_020_pwa_statique_deployable_local_first - PWA statique deployable local-first
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: High
> Theme: Operator workflow and runtime integration
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
Les spikes 0.1 et 0.2 prouvent la faisabilité technique du moteur local, mais
ils ne constituent pas encore une PWA distribuable. Le jalon 0.3 doit produire un
artefact statique, installable et testable, avec les contrôles minimaux de
workspace/quota et une documentation de déploiement Caddy suffisamment claire
pour servir l'outil depuis `paulmondou.fr` ou un sous-domaine.

# Scope
- In:
  - Définir un build statique reproductible pour la PWA local-first.
  - Ajouter manifest PWA, icônes/assets minimaux et service worker.
  - Cacher l'app shell, pas les traces utilisateur par défaut.
  - Intégrer le moteur local 0.2 dans une UI statique utilisable.
  - Ajouter workspace list/resume/delete/purge, et export/import minimal ou
    format documenté avec décision de report explicite.
  - Ajouter détection ou simulation de quota storage et messages de récupération.
  - Documenter Caddy/static hosting pour `paulmondou.fr` ou sous-domaine.
  - Ajouter smoke Chromium sur les fichiers buildés, manifest et service worker.
- Out:
  - Full migration de l'UI principale FastAPI.
  - Parité DBC exhaustive.
  - Support mobile/tablette pour grosses traces.
  - Synchronisation cloud ou comptes utilisateurs.
  - Déploiement réel production sans demande explicite.

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

# AC Traceability
- request-AC1 -> This backlog slice. Proof: AC1 requires static build output.
- request-AC2 -> This backlog slice. Proof: AC2 requires no-backend static workflow.
- request-AC3 -> This backlog slice. Proof: AC3 requires manifest/service worker/offline app shell.
- request-AC4 -> This backlog slice. Proof: AC4 requires minimal workspace lifecycle.
- request-AC5 -> This backlog slice. Proof: AC5 requires quota/storage recovery behavior.
- request-AC6 -> This backlog slice. Proof: AC6 requires Caddy/static deployment documentation.
- request-AC7 -> This backlog slice. Proof: AC7 requires build, browser/local tests, smoke and PWA checks.
- request-AC8 -> This backlog slice. Proof: AC8 requires documented remaining adoption limits.

# Decision framing
- Product framing: Not needed
- Product signals: (none detected)
- Product follow-up: No product brief follow-up is expected based on current signals.
- Architecture framing: Not needed
- Architecture signals: (none detected)
- Architecture follow-up: No architecture decision follow-up is expected based on current signals.

# Links
- Product brief(s): (none yet)
- Architecture decision(s): (none yet)
- Request: `req_010_pwa_statique_deployable_local_first`
- Roadmap: `road_001_architecture_pwa_spa_local_first`
- Primary task(s): `task_020_pwa_statique_deployable_local_first`

# AI Context
- Summary: Backlog slice for roadmap milestone 0.3, packaging the local
  ASC/DBC engine as a static installable PWA with workspace lifecycle, quota
  recovery, Caddy hosting docs and browser smoke validation.
- Keywords: backlog-groom, pwa, static build, service worker, manifest,
  local-first, workspace, quota, caddy, smoke, deployment
- Use when: Implementing or reviewing the 0.3 static deployable PWA milestone.
- Skip when: Working on deeper local engine parity or the FastAPI local server.

# Priority
- Priority: High
- Rationale: This is the delivery packaging gate that turns the validated local
  engine into something that can be hosted and exercised like the target product.

# Notes
- Hybrid rationale: Derived from request `req_010_pwa_statique_deployable_local_first` and kept bounded to one coherent delivery slice.
- Source file: `logics/request/req_010_pwa_statique_deployable_local_first.md`.
- Generated locally by logics-manager.
- Task `task_020_pwa_statique_deployable_local_first` was finished via `logics-manager flow finish task` on 2026-07-22.

# Tasks
- `task_020_pwa_statique_deployable_local_first`
