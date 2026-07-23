## item_029_repondre_a_l_audit_code_du_23_juillet_2026 - Repondre a l audit code du 23 juillet 2026
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
- L audit code du 23 juillet 2026 identifie un risque de gel global DuckDB pendant les exports CSV/wide, des messages d erreur pouvant exposer des chemins locaux et une limite d upload non bornee au niveau requete.
- Plusieurs constats moyens peuvent produire des resultats incoherents ou des garanties de securite ambigues : decimation SQL avec floats interpoles, filtre signal vide dependant du decodage paresseux, token en query string, lecture locale arbitraire documentee seulement par convention, et en-tetes `Host`/`Origin` absents acceptes.
- La reponse doit rester un lot de durcissement code/test/docs coherent, sans convertir CanTraceDiag en application distante multi-utilisateur.

# Scope
- In:
  - Corriger H1, S1 et S3 avec tests de regression explicites.
  - Traiter M1 et M2 avec tests couvrant les entrees degeneres et les filtres sans correspondance.
  - Trancher S2/S4/S5 par correctif minimal ou documentation threat model testee.
  - Ajouter les fixtures/tests manquants signales par l audit lorsque le risque est borne.
  - Nettoyer les doublons ou code mort simples si cela reduit la dette sans refonte large.
  - Mettre a jour les docs projet lorsque le comportement local-first ou les limites d import changent.
- Out:
  - Refonte complete de `create_app` ou decomposition exhaustive de toutes les closures.
  - Nouveau modele d authentification distant ou gestion multi-utilisateur.
  - Hebergement public, packaging PWA ou parite navigateur, deja suivis par les chaines PWA.
  - Installation locale du navigateur Playwright si elle n est pas necessaire aux tests cibles de ce lot.

# Acceptance criteria
- AC1: H1 est resolu par un export CSV/wide qui libere le verrou store avant ou pendant le streaming HTTP sans bloquer `/api/series`, `/api/cursor` ou `/api/trace`.
- AC2: S1 est resolu par une normalisation des erreurs DBC/import qui preserve un detail utile sans chemin local absolu, WSL, POSIX, Windows ou chemin temporaire.
- AC3: S3 est resolu par un compteur cumulatif par requete d upload couvrant trace plus DBC multiples et par un test de depassement agregat.
- AC4: M1/M2 sont corriges avec requetes parametrees, gestion explicite des timestamps degeneres et resultat vide stable quand aucun signal catalogue ne matche.
- AC5: S2/S4/S5 ont une decision implementee : politique token/query, import local arbitraire et headers absents sont coherents entre code, CLI, README/docs et tests.
- AC6: Les lacunes de tests listees dans l audit sont fermees pour les corrections retenues, et les nettoyages L4/L5/L6/L3/L2/L1 sont faits ou reportes dans une note justifiee.
- AC7: La livraison est verifiee par `ruff check .`, `pytest` ou un sous-ensemble cible justifie, et par `logics-manager lint --require-status` + `logics-manager audit --group-by-doc`.

# AC Traceability
- request-AC1 -> This backlog slice. Proof: AC1 covers H1 export streaming lock release and concurrency proof.
- request-AC2 -> This backlog slice. Proof: AC2 covers S1 sanitized DBC/import errors and non-leak tests.
- request-AC3 -> This backlog slice. Proof: AC3 covers S3 aggregate upload budget and regression test.
- request-AC4 -> This backlog slice. Proof: AC4 covers M1/M2 correctness fixes and deterministic empty results.
- request-AC5 -> This backlog slice. Proof: AC5 covers S2/S4/S5 policy decisions in code/docs/tests.
- request-AC6 -> This backlog slice. Proof: AC6 covers low-risk cleanup or explicit deferral.
- request-AC7 -> This backlog slice. Proof: AC7 defines validation commands and Logics checks.

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
- Request: `req_014_repondre_a_l_audit_code_du_23_juillet_2026`
- Primary task(s): `task_030_repondre_a_l_audit_code_du_23_juillet_2026`

# AI Context
- Summary: Backlog slice for code hardening after `docs/audit-code-2026-07-23.md`.
- Keywords: audit-code-2026-07-23, H1, S1, S3, M1, M2, streaming-export, sanitized-errors, aggregate-upload-limit
- Use when: Implementing or reviewing the audit response hardening slice.
- Skip when: The change belongs to the PWA hosting/parity chains or unrelated feature work.

# Priority
- Priority: High
- Rationale: H1 can freeze all store-backed API requests during slow exports, while S1/S3 affect local-path disclosure and disk exhaustion risk.

# Notes
- Hybrid rationale: Derived from request `req_014_repondre_a_l_audit_code_du_23_juillet_2026` and kept bounded to one coherent delivery slice.
- Source file: `logics/request/req_014_repondre_a_l_audit_code_du_23_juillet_2026.md`.
- Generated locally by logics-manager.
- Source audit: `docs/audit-code-2026-07-23.md`.
- Recommended execution order: H1, S1, S3, M1/M2, S2/S4/S5, then low-risk cleanups.
- Task `task_030_repondre_a_l_audit_code_du_23_juillet_2026` was finished via `logics-manager flow finish task` on 2026-07-23.

# Tasks
- `task_030_repondre_a_l_audit_code_du_23_juillet_2026`
