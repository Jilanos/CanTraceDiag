# ADR 0004 - Traces, DBC et configs CANalyzer hors dépôt

## Statut

Accepté

## Contexte

Les traces et DBC ne sont pas jugées hautement confidentielles, mais elles sont volumineuses, changeantes et liées à des acquisitions locales. Elles ne doivent pas être versionnées dans le dépôt applicatif.

## Décision

Le dépôt contient le code, la documentation, les tests synthétiques et les spécifications. Les traces, DBC, caches et configurations CANalyzer restent locales et ignorées par Git.

## Conséquences

- Le dépôt peut être public.
- Les tests automatisés devront utiliser de petits fixtures synthétiques ou anonymisés.
- La documentation peut citer les ordres de grandeur observés sans embarquer les fichiers source.
