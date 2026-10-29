# Polices embarquées

Les polices sont versionnées dans le kit (jamais chargées depuis un CDN) afin que le PDF soit
identique sur le runner, en Docker et en local. Un graissage normal et un gras par famille.
Conversion TTF vers WOFF2 par `fonttools` (sans modification des glyphes ni des noms) ; le texte
intégral de chaque licence est conservé à côté des fichiers.

| Famille | Fichiers | Version | Licence | Source |
| --- | --- | --- | --- | --- |
| Liberation Sans (métriques d'Helvetica, comme `helvet` de `macros.sty`) | `LiberationSans-Regular.woff2`, `LiberationSans-Bold.woff2` | 2.1.5 | SIL Open Font License 1.1 (`OFL-LiberationSans.txt`) | https://github.com/liberationfonts/liberation-fonts/releases/tag/2.1.5 (archive `liberation-fonts-ttf-2.1.5.tar.gz`) |
| Inconsolata (police du `zi4` de `macros.sty`) | `Inconsolata-Regular.woff2`, `Inconsolata-Bold.woff2` | 3.000 | SIL Open Font License 1.1 (`OFL-Inconsolata.txt`) | https://github.com/googlefonts/Inconsolata/releases/tag/v3.000 (archive `fonts_ttf.zip`) |

Copyright : Liberation Sans, © 2012 Red Hat, Inc. (nom réservé « Liberation »), données © 2010
Google Corporation ; Inconsolata, © 2006 The Inconsolata Project Authors.
