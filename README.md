# cielir-cours-kit

Outillage commun des dépôts de cours du **BTS CIEL option Informatique et Réseaux**, lycée Louis Rascol, Albi.

Un dépôt de cours ne contient que son contenu : le cours en Markdown, son diaporama, ses métadonnées. Mise en page, génération des PDF, thème des slides, publication — tout le reste vit ici, en un seul endroit, et sert tous les cours à la fois.

## Ce que le kit produit

À partir de trois fichiers seulement (`cours.yml`, `COURS.md`, `slides/NN-*.md`) :

| Document | Contenu |
| --- | --- |
| `cours.pdf` | la fiche de cours complète, réponses comprises |
| `cours-a-trous.pdf` | la même fiche, trous vides — l'exemplaire imprimé et distribué |
| `slides.pdf` | le diaporama |
| les slides en HTML | mises en ligne sur GitHub Pages |

Les deux fiches sortent du **même** `COURS.md` : une seule source, deux rendus. Un corrigé ne peut donc pas diverger de l'exemplaire des étudiants.

## Écrire un cours

### Les trous

Dans `COURS.md`, ce que l'étudiant doit écrire va entre `<ins>` et `</ins>` :

```markdown
Le code source est écrit dans un langage de <ins>haut</ins> niveau.
```

Document complet : la réponse apparaît. Document à trous : un pointillé dont la longueur est calculée d'après la réponse.

Pour une réponse rédigée, sur plusieurs lignes, la même balise porte le nombre de lignes à laisser à l'étudiant et occupe un paragraphe à elle seule :

```markdown
*Que signifie l'option `-Wall` ?*

<ins lignes="2">`-Wall` demande au compilateur de signaler tous les avertissements.</ins>
```

Document complet : la réponse, dans un encadré. Document à trous : deux lignes réglées. La réponse est du texte en ligne (gras, code…), sur une ou plusieurs lignes de source ; elle ne peut pas contenir de bloc (liste, bloc de code).

Une seule balise, donc : `<ins>` court dans une phrase, `<ins lignes="n">` long dans son paragraphe. C'est voulu : `COURS.md` se lit aussi sur github.com, où la balise s'affiche comme un trou souligné, sans rien qui ressemble à du gabarit.

Une balise mal formée (non appariée, imbriquée, à cheval sur deux paragraphes, nombre de lignes qui n'est pas un entier positif) arrête la génération avec un message : jamais une réponse ne passe en clair dans le document à trous.

### Les encadrés

Les cinq alertes GitHub deviennent des encadrés : `> [!NOTE]`, `> [!TIP]`, `> [!IMPORTANT]`, `> [!WARNING]`, `> [!CAUTION]`. Chacun porte son titre en lettres : le document s'imprime en noir et blanc, la couleur ne doit jamais porter seule l'information.

### Les blocs de code

Un bloc dont le langage est `terminal` est rendu comme une session de terminal ; les autres langages sont colorés.

Dans un bloc `terminal`, et là seulement, `<ins>` est un trou comme dans le texte courant :

````markdown
```terminal
$ g++ -Wall -o <ins>age</ins> age.cpp
```
````

Le blanc occupe autant de caractères que la réponse. Dans tout autre bloc, `<ins>` reste du texte.

Un paragraphe immédiatement suivi d'un tableau, d'une figure ou d'un bloc de code reste avec lui d'une page à l'autre : la consigne n'est jamais séparée de son exercice.

### Les schémas

Dans un SVG, tout élément portant la classe `remplissable` est **retiré** du document à trous. Un seul schéma sert donc aux deux versions : les étiquettes à compléter disparaissent de l'exemplaire des étudiants.

## Publier un cours

Copier `gabarits/publier.yml` dans `.github/workflows/publier.yml`, régler une fois *Settings > Pages > Source* sur « GitHub Actions », puis pousser un tag :

```bash
git tag v1.01 && git push origin v1.01
```

Le workflow contrôle qu'aucune information personnelle ne traîne, fabrique les trois PDF, met les slides en ligne et crée la release avec les PDF attachés. Rien de généré n'entre jamais dans le dépôt.

## Les versions

`vX` est la mouture d'une promotion (`v1` = 2026-2028) ; `vX.YY` en est une retouche de cours d'année (`v1.01`, `v1.02`…). Un tag mal formé arrête la publication avec un message qui dit ce qui est attendu.

La version et sa date n'apparaissent **jamais** dans les sources : elles sont injectées à la génération et ne vivent que dans les documents de la release. Un `COURS.md` n'a donc pas à être retouché pour être republié.

## Le standard d'un dépôt de cours

Un dépôt par séance, nommé `<séquence>-c<NN>-<séanceCamelCase>` : `linux-c06-scriptsBash`, `git-c01-decouverte`, `cpp-c04-tableauxVecteurs`.

```text
cpp-c04-tableauxVecteurs/
├── README.md                     présentation, déroulé, crédits, licence
├── cours.yml                     métadonnées du bloc
├── COURS.md                      le cours — source unique des deux fiches
├── slides/
│   ├── 04-tableauxVecteurs.md    deck Marp
│   └── img/                      SVG et images, partagés avec la fiche
├── .vscode/settings.json         thème Marp pour l'aperçu dans VS Code
├── .vscode/extensions.json       recommande l'extension Marp for VS Code
└── .github/workflows/publier.yml copie de gabarits/publier.yml
```

Pas de `themes/`, pas de `build.sh`, pas de `scripts/`, pas de `output/` : le dépôt ne porte aucun outil et aucun fichier généré.

## Aucune information personnelle

Ces dépôts sont partagés aux étudiants. Le contrôle refuse adresses de courriel et numéros de téléphone, et s'exécute avant toute publication :

```bash
uv run cielir-cours verifier .
```

Un faux positif se déclare dans `.cielir-ignore`, à la racine du dépôt contrôlé.

## En local

Ni Node ni LaTeX ne sont nécessaires : le rendu papier est en Python, Marp tourne dans Docker.

```bash
make test       # les tests du kit
make temoin     # régénère le dépôt témoin : les trois PDF dans build/temoin/
make slides     # le diaporama seul
make clean
```

Pour un autre dépôt que le témoin : `make temoin DEPOT=../cpp-c04-tableauxVecteurs`.

## Le dépôt témoin

`temoin/` est un cours jouet qui exerce toute la mise en page : trous, lignes de réponse, les cinq encadrés, tableau à trous, bloc terminal, code coloré, schéma à compléter. Le tag `v1` du kit ne bouge qu'après l'avoir régénéré sans régression — et relu à l'œil, en couleur puis en niveaux de gris.

## Pourquoi ce dépôt est public

Une action composite hébergée dans un dépôt *internal* n'est pas résolvable depuis un dépôt public : les dépôts de cours, eux, sont publics. Le kit est donc public lui aussi. Il ne contient que du thème, du CSS et des scripts — aucune donnée d'établissement, aucune donnée personnelle.

## Licence

[CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/deed.fr)
