<!--
Gabarit du README d'un dépôt de cours. À copier en README.md, puis remplacer tout ce qui
est entre guillemets «…» et supprimer ce commentaire.

Trois règles qui ne se négocient pas :
  1. aucune information personnelle — ni nom d'enseignant, ni courriel, ni téléphone ;
  2. aucune version ni date ici — elles ne vivent que dans les documents de la release ;
  3. les crédits d'images sont obligatoires, avec auteur, licence et source.
-->

# «Séquence» — c«NN» : «Titre de la séance»

**«Discipline» — «Classe»** · «Établissement»

📽️ **Les slides : <https://ciel-ir-rascol.github.io/«nom-du-depot»/>**
📄 **Les fiches en PDF : [dernière release](https://github.com/ciel-ir-rascol/«nom-du-depot»/releases/latest)**

Cours d'environ **«durée»** qui introduit le TP «dépôt du TP». Public : «ce que les étudiants savent déjà, ou pas».

Le dépôt contient :

- les **slides** du cours (Marp), avec les notes du présentateur ;
- la **fiche de cours**, distribuée à trous : les étudiants la complètent pendant la projection et la gardent comme aide-mémoire.

Les deux fiches — complète et à trous — sortent du même `COURS.md` et sont attachées à chaque release.

## Capacités visées

- «capacité, reprise de cours.yml»
- «capacité»

## Déroulé («durée»)

| Partie | Contenu | Slides | Durée indicative |
| :---: | --- | :---: | :---: |
| — | «accroche» | «1–4» | «5 min» |
| 1 | «contenu» | «5–14» | «15 min» |
| 2 | «contenu» | «15–24» | «15 min» |
| — | À retenir, transition vers le TP, crédits | «25–27» | «5 min» |

## Arborescence

```text
.
├── cours.yml                        métadonnées du bloc
├── COURS.md                         le cours — source unique des deux fiches
├── slides/
│   ├── «NN»-«séance».md             source des slides (Marp)
│   └── img/                         schémas SVG et images
├── .vscode/settings.json            thème Marp pour l'aperçu dans VS Code
└── .github/workflows/publier.yml    publication sur tag
```

Aucun fichier généré n'est enregistré ici : les PDF et les slides en ligne sont produits à la publication.

## Travailler le cours

L'aperçu des slides se fait dans VS Code avec l'extension **Marp for VS Code** ; le thème `ciel` est déjà déclaré dans `.vscode/settings.json`.

Pour régénérer les trois PDF en local, depuis une copie du kit :

```bash
make temoin DEPOT=../«nom-du-depot»
```

### Publier

```bash
git tag v1.01 && git push origin v1.01
```

`vX` est la mouture d'une promotion, `vX.YY` une retouche de cours d'année. Le reste est automatique : contrôle de confidentialité, trois PDF, slides en ligne, release. Réglage à faire une fois : *Settings > Pages > Source* = « GitHub Actions ».

L'outillage vit dans [`cielir-cours-kit`](https://github.com/ciel-ir-rascol/cielir-cours-kit).

## Crédits des images

| Image | Auteur | Licence | Source |
| --- | --- | --- | --- |
| «image» | «auteur» | «licence» | [«où»](«URL») |
| Schémas (`slides/img/*.svg`) | auteur du cours | CC BY-NC-SA 4.0 | ce dépôt |

«Les licences propres des images s'appliquent indépendamment de celle du cours.»

## Licence

[CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/deed.fr)
