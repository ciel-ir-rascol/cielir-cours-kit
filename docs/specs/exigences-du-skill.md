# Ce que le skill `cours-cielir` doit dire

Mémoire de ce qui a été appris en construisant le kit et les trois premiers cours. Le skill
(tâche 13 du plan) se rédige à partir d'ici : ce document survit à l'espace de travail SDD,
qui est supprimé à la clôture.

Le skill a trois modes — **créer** un cours, **mettre en conformité** un dépôt existant,
**convertir** un article du site. Les règles ci-dessous valent pour les trois sauf mention.

## Les règles qui ne se déduisent pas du kit

- **Nommage** : `<séquence>-c<NN>-<séanceCamelCase>`, dans `/home/joris/repos/cielir`, remote
  sur l'organisation `ciel-ir-rascol`.
- **Ce qu'un dépôt de cours contient** : `cours.yml`, `COURS.md`, `slides/NN-<séance>.md`,
  `slides/img/`, `.vscode/`, `.github/workflows/publier.yml`, `README.md`. Et rien de généré.
- **Les TP restent dans leurs dépôts.** Un cours cite le TP **par le nom de son dépôt**
  (`cpp-tp03-tableauxVecteurs`), jamais par le titre de son README.
- **Versions** : tag `vX.YY`. `vX` est la mouture d'une promotion, `vX.YY` une retouche de
  l'année. La version et la date ne vivent **que** dans les documents de la release, jamais
  dans une source.
- **Aucune information personnelle** : ni courriel, ni téléphone, ni chemin local. Le nom de
  l'auteur (`auteur` dans `cours.yml`) est la seule exception, et c'est une signature, pas un
  moyen de contact. La liste `noms` de `motifs.yml` ne doit jamais contenir ce nom, sinon le
  contrôle refuserait la signature du support.
- **Aucune licence de l'auteur sur un support.** Les crédits d'images d'autrui, avec leur
  licence, sont en revanche obligatoires : c'est la condition d'emploi de ces images.
- **Les dépôts de cours sont privés**, lus par l'équipe GitHub de la promotion ; le kit reste
  public (voir « Le piège de la visibilité » plus bas).
- **La version du kit attendue** : l'action est épinglée sur le tag flottant `v1`.

## Lire le cours d'avant et celui d'après — étape obligatoire

C'est la leçon la plus rentable de tout le projet. Un cours ne se juge pas seul : ses défauts
les plus coûteux ne se voient que depuis ses voisins dans la progression, qui vivent dans
`ciel-ir-rascol.github.io/docs/<séquence>/NN-<séance>/` — et c'est le **diaporama** qui porte
le contenu, le `.md` n'étant qu'un lien.

Quatre questions, dans cet ordre :

1. **Les capacités sont-elles tenables à ce point de la progression ?** Vérifier le numéro des
   cours où vivent les notions supposées, pas leur ordre intuitif.
2. **Qu'a-t-on enseigné juste avant, qui servirait ici et qu'on n'utilise pas ?**
3. **Un mot change-t-il de sens d'un cours à l'autre ?**
4. **Le cours contredit-il une règle enseignée avant ?**

Détail et exemple vécu : `procedure-mise-en-conformite.md`, §0.1.

## Les pièges qui ont coûté cher

- **Une capacité ne doit jamais épeler une réponse que la fiche troue.** Le cartouche les
  imprime en haut de la première page, y compris celle de la fiche à trous.
- **Le kit se tague et se valide avant le cours, jamais l'inverse.** Publier un cours alors
  que `v1` pointe sur un kit qui ignore une nouveauté casse la publication. L'ordre est :
  pousser le kit, déplacer `v1`, republier le **témoin**, vérifier, puis les vrais cours.
- **Rendre un dépôt privé ne rend pas son site Pages privé.** Il faut
  `PUT /repos/{o}/{r}/pages -F public=false` en plus, sinon les slides restent lisibles de
  quiconque a l'URL.
- **Un dépôt neuf n'autorise que `branch main` à déployer Pages.** Sans la politique
  `tag v*` ajoutée à l'environnement `github-pages`, le job `pages` échoue sur un tag.
- **`gh repo edit --visibility`** réclame `--accept-visibility-change-consequences`.
- **Une action d'un dépôt privé n'est utilisable que par un appelant privé.** Mais la vraie
  contrainte sur le kit n'est pas là : c'est le `git ls-remote` **anonyme** qui lit son SHA
  pour les notes de release. Si le kit doit un jour devenir privé, c'est cette ligne-là qu'il
  faut changer, et elle seule.
- **`cp -R source destination`** copie *dans* la destination quand elle existe déjà. Vider
  d'abord, sinon les images du diaporama se retrouvent dans `slides/img/img/` et disparaissent
  sans que rien n'échoue.
- **`COURS.md` ne se lit pas sur GitHub.** Aucun HTML n'est interprété dans un bloc de code,
  donc les trous s'y affichent en clair. Le document que lisent les étudiants est la **fiche
  en ligne**, pas la source. Ne jamais les y envoyer.

## Contrôler avant de publier

- `cielir-cours verifier <dépôt>` : aucune information personnelle.
- **Contrôle de fuite sur la release publiée**, pas sur une génération locale. Le script de
  référence connaît les trois sources de faux positifs qui ont piégé à répétition :
  1. les **étiquettes des SVG**, qui sont des `<img>` dans le HTML mais du texte dans le PDF ;
  2. l'**en-tête courant**, écrit une fois dans le HTML et répété à chaque page ;
  3. **Pygments découpe un littéral en jetons** que l'extraction du PDF recolle — comparer des
     textes privés de tout espace.
- **Regarder les documents.** Un comptage d'occurrences ne distingue pas une redite voulue
  d'une réponse donnée, et une mesure peut mentir : vérifier qu'une page de contrôle charge
  bien sa feuille de style, et se méfier d'une recherche de texte brut dans du HTML où le gras
  a coupé la chaîne. **Quand la mesure contredit ce qu'on voit, regarder la mesure en premier.**

## Écrire le contenu

- **Une source, plusieurs rendus.** `COURS.md` produit la fiche papier à trous, la fiche
  remplie et la page web. Les passages propres à un support se marquent
  `<div class="ecran">` et `<div class="papier">` ; le reste paraît partout.
- **La fiche papier reste compacte** (quatre pages environ) ; les développements vont en
  `ecran`. La page web est le cours de référence pendant le TP.
- **Les exercices (« À vous de jouer ») sont réservés au papier** : avec les réponses
  affichées, ce n'est plus un exercice mais une liste d'affirmations.
- **Une partie « L'essentiel » clôt le cours** : un mémo de syntaxe, sans trou, sur les deux
  supports.
- **Un trou doit porter sur un mot à retenir, et ne pas être lisible ailleurs.** Si une
  réponse doit forcément paraître en clair — un nom de méthode qu'un exercice est obligé
  d'écrire pour poser sa question — ce n'est pas l'exercice qu'on change, c'est le trou qu'on
  déplace.
- **Une demande d'exercice doit être satisfaisable** : si la réponse attendue nomme une
  variable, la demande doit la nommer aussi.
- **Ne pas répliquer un registre d'écriture avant qu'il soit validé sur un cas.** Rédiger
  deux cours dans un style que l'enseignant n'a pas encore lu, c'est préparer deux réécritures.
- **Le diaporama suit la fiche.** Toute partie ajoutée au cours qui doit être projetée demande
  sa slide, et le déroulé du README se recale sur le nouveau compte. À la fin d'une passe de
  rédaction, comparer les deux plans côte à côte : c'est ainsi qu'on s'aperçoit qu'une synthèse
  ou un mémo n'existe que sur le papier.
- Le fond du cours appartient à l'enseignant. On propose une passe, il corrige.

## Images et icônes : la licence d'abord, le rendu ensuite

- **Établir la licence sur pièces avant de poser une image**, en lisant les conditions de la
  source, pas en se fiant à l'usage courant. Trois cas déjà tranchés :
  - **logo C++** (`isocpp/logos`, Jeremy Kratz) : la Standard C++ Foundation autorise
    explicitement l'emploi dans un support pédagogique sur le C++ normalisé, **sans
    modification** et sans sous-entendre une approbation. Crédit obligatoire ;
  - **marque GitHub** (`brand.github.com`) : utilisable **pour pointer un dépôt**, jamais
    recolorée ni redimensionnée hors proportions. Les deux variantes sont embarquées, la
    blanche pour les fonds sombres, la noire pour les fonds clairs ;
  - **icônes des encadrés** : Bootstrap Icons, **MIT** — préféré au CC BY de Font Awesome,
    qui aurait imposé une ligne de crédit visible sur chacun des cours. MIT permet la
    modification : seule la couleur l'est, jamais le tracé.
- **Une icône plutôt qu'un caractère.** Un caractère dépend de ce que la police couvre, et la
  police de secours de WeasyPrint (DejaVu Sans) n'a ni 💡, ni ❗, ni ⛔ : ils sortent en carré
  vide sur le PDF, tout en apparaissant dans la couche texte — donc invisibles à un contrôle
  qui ne fait que chercher le caractère. Les icônes sont embarquées en URI de données dans les
  deux feuilles, avec leurs fichiers d'origine conservés comme source traçable.
- **Le même signe sur les deux supports.** Un encadré doit se reconnaître de la même façon en
  cours et à la maison.

## Ce que le kit produit, et qu'il ne faut pas refaire à la main

- Le **numéro** des parties et des sous-parties, par compteurs CSS — jamais dans la source :
  un `## 1. Titre` donnerait « 1. 1. Titre ».
- Le **sommaire** de la fiche en ligne, à deux niveaux, avec ses ancres.
- Le **cartouche**, la page de titre du deck, le pied de page, la signature et la release.
