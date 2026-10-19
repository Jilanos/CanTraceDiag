# ADR 0008 - Livraison Windows autonome et traces ASC jusqu'à 1 Gio

## Statut

Accepté

## Contexte

Le produit déployé est la PWA statique (voir `docs/architecture-pwa-canonique.md`).
Elle lit la trace entière en mémoire du navigateur (`File.text()`, découpage,
décodage d'échantillons) et ne peut pas tenir une acquisition ASC de 1 Gio. Le
moteur Python/FastAPI, lui, importe déjà en flux vers un index DuckDB sur disque,
mais il n'était utilisable sous Windows qu'à travers WSL et un environnement
virtuel installé à la main. Un opérateur qui n'a que Windows et un navigateur ne
pouvait donc pas analyser une grosse acquisition (req_034).

## Décision

1. **Exécutable portable Windows x64.** `CanTraceDiag-<version>-windows-x64.exe`
   est produit par PyInstaller (un seul fichier, console visible) à partir de
   `packaging/windows/CanTraceDiag.spec`, avec un jeu de dépendances épinglé
   (`packaging/windows/constraints.txt`). Il embarque Python, FastAPI/Uvicorn,
   DuckDB, PyArrow, les lecteurs ASC/TRC/BLF/MF4 et l'UI statique. Pas de moteur
   web de bureau : l'interface reste celle du navigateur par défaut.
2. **Service loopback et cycle de vie explicite** (`cantracediag.desktop`) :
   dossier par utilisateur `%LOCALAPPDATA%\CanTraceDiag` (données, journaux,
   `instance.json`), port réservé par un vrai `bind` (les plages réservées par
   Hyper-V/WSL font échouer un port qui paraît libre), réouverture d'une instance
   de même version, refus explicite d'une autre version, arrêt par la fermeture
   de la console, Ctrl+C ou `--stop` (`/api/shutdown`, jeton requis).
3. **Chemins natifs.** Un backend Windows ne réécrit plus `C:\...` ni
   `\\serveur\partage\...` en chemins `/mnt/...` ; la conversion WSL ne s'applique
   qu'à un backend Linux.
4. **Budgets d'upload indépendants et appliqués en flux** (`cantracediag.upload`) :
   trace ≤ 1 073 741 824 octets (inclusif), DBC téléversés ≤ 64 Mio au total,
   enveloppe multipart ≤ 8 Mio, requête ≤ leur somme. Le corps est analysé au fil
   de l'eau vers un dossier de staging par utilisateur, au lieu d'être d'abord
   mis en tampon entier par Starlette. Annulation pendant le transfert, ENOSPC
   traduit en erreur actionnable (507), staging purgé au démarrage. En mode LAN,
   sans réglage explicite, l'ancien plafond agrégé de 512 Mio est conservé.
5. **Distribution sans binaire dans Git.** `CanTraceDiag.cmd` (racine) délègue à
   `packaging/windows/launcher.ps1`, qui résout la release `v<version>` de la
   copie de travail, vérifie la provenance (version, tag, x64, commit exact) et le
   SHA-256 avant toute exécution, puis met l'exécutable vérifié en cache par
   utilisateur (réutilisé hors ligne). Un commit de développement sans binaire
   publié échoue avec la marche à suivre ; jamais de repli sur « latest ».
6. **CI et release découplées du déploiement web.** Le workflow réutilisable
   `.github/workflows/windows.yml` construit, teste (smoke sans Python dans
   l'environnement, lanceur contre une release locale) et publie en artefact le
   fichier exact ; le tag publie cet artefact (exe, `.sha256`, provenance,
   notices) dès que la validation et ce build passent, indépendamment du
   déploiement de la PWA.

## Conséquences

- La PWA hébergée reste inchangée et reste le produit web canonique ; sa limite
  de taille, liée à la mémoire du navigateur, n'est pas relevée.
- La garantie 1 Gio porte sur l'ASC. TRC, BLF et MF4 brut sont conservés dans
  l'exécutable sans garantie de taille.
- L'exécutable n'est pas signé : SmartScreen peut l'intercepter au premier
  lancement. La vérification SHA-256 du lanceur est la garantie d'intégrité ;
  aucune protection Windows n'est contournée.
- asammdf et python-can (LGPL) sont embarqués sans modification ;
  `THIRD_PARTY_NOTICES.txt` et le script de build permettent de reconstruire
  l'exécutable avec une autre version de ces bibliothèques.
- La qualification pleine taille (`scripts/qualify_windows_large_asc.py` sur une
  fixture de `scripts/generate_large_asc.py`) mesure import, mémoire, latences,
  annulation et fidélité trame à trame sur l'exécutable gelé.
