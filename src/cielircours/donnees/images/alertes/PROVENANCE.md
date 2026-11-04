# Icônes des encadrés

Les cinq fichiers de ce dossier viennent de [Bootstrap Icons](https://github.com/twbs/icons),
sous **licence MIT** (Copyright 2019-2024 The Bootstrap Authors), et sont repris tels quels.

| Fichier | Encadré |
| --- | --- |
| `info-circle-fill.svg` | Note |
| `lightbulb-fill.svg` | Astuce |
| `exclamation-circle-fill.svg` | Important |
| `exclamation-triangle-fill.svg` | Attention |
| `x-octagon-fill.svg` | Danger |

Ils ne sont pas lus à l'exécution : les feuilles `cours.css` et `site.css` en portent une copie
en URI de données, avec la couleur de l'encadré substituée à `currentColor` — une URI de
données ne sait pas résoudre `currentColor`. Ces fichiers sont la **source traçable** des
données embarquées ; si l'on change une icône, on remplace ici d'abord, puis on régénère les
règles CSS.

La licence MIT autorise la modification : seule la couleur l'est, jamais le tracé.
