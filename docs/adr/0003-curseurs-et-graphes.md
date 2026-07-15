# ADR 0003 - Subplots temporels et curseurs par valeur la plus proche

## Statut

Accepté

## Contexte

L'expérience attendue est proche de CANalyzer Graph : plusieurs signaux visibles sur un axe temporel commun, plutôt que des courbes toutes superposées avec plusieurs axes Y. Le besoin n'inclut pas de replay dynamique.

## Décision

- Afficher les signaux en subplots empilés avec axe X temporel commun.
- Utiliser un subplot par signal par défaut.
- Prévoir une option de superposition sur un axe commun lorsque plusieurs valeurs sont compatibles.
- La valeur au curseur est l'échantillon le plus proche du timestamp curseur.
- Ne pas interpoler les valeurs dans le MVP.

## Conséquences

- Le comportement curseur est simple, déterministe et cohérent avec des signaux CAN discrets.
- Les deltas entre deux curseurs se calculent sur les échantillons les plus proches.
- L'UI devra gérer beaucoup de subplots avec des hauteurs compactes et lisibles.
