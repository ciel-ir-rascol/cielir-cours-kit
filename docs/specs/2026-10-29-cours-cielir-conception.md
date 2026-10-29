# Conception — dépôts de cours CIEL-IR, kit central et skill `cours-cielir`

**Date :** 29 octobre 2026
**Statut :** conception validée, implémentation non commencée
**Périmètre :** le standard des dépôts de cours, le dépôt `cielir-cours-kit` qui le met en œuvre, et le skill Claude Code qui crée et maintient ces dépôts.

---

## 1 — Intention

Les cours de BTS CIEL option IR du lycée Louis Rascol vivaient jusqu'ici dans un site mkdocs unique, `ciel-ir-rascol.github.io`, où toutes les séquences et toutes les années partageaient une seule navigation. Les TP, eux, sont déjà des dépôts GitHub distincts que les étudiants forkent et qui servent de rendu.

On veut que les cours suivent le même principe : **un dépôt par bloc de cours**. Un bloc, c'est l'unité pédagogique que l'enseignant projette en classe — « Découverte de Git », « Scripts Bash » — même quand elle occupe deux séances de quatre heures.

Ce que ça apporte :

- un cours se corrige, se tague et se publie sans toucher aux autres ;
- l'étudiant reçoit une adresse par cours, référencée dans sa progression sur `tracker` ;
- chaque publication est une **version datée**, ce qui rend lisible ce qui a changé entre deux promotions ;
- le même dépôt porte les trois supports d'une séance : ce qui est projeté, ce qui est lu, ce qui est écrit à la main.

Le dépôt `git-cours01-decouverte` est l'ébauche de ce standard : il a déjà les slides Marp, le thème `ciel`, le workflow Pages et un document à trous. Ce qui lui manque, et que cette conception apporte : une source unique en markdown, la suppression de LaTeX, les versions par tag, et la mutualisation de l'outillage.

---

## 2 — Objectifs

1. Un dépôt par bloc de cours, nommé selon une règle unique, hébergé sur `ciel-ir-rascol` et cloné dans `/home/joris/repos/cielir/`.
2. Un dépôt de cours ne contient **que du contenu** : le cours, les slides, les images, une config. Aucun outil, aucun thème, aucun fichier généré.
3. Une **signature visuelle unique**, identique sur les slides projetées et sur le document papier, reconnaissable d'un dépôt à l'autre.
4. Des **versions** : chaque publication est un tag git, et produit une release GitHub portant les PDF.
5. **Aucune information personnelle enseignante** dans les dépôts, qui sont publics et partagés aux étudiants.
6. Un **document papier à trous**, que les étudiants complètent pendant que le cours est projeté, et qui leur sert ensuite d'aide-mémoire.
7. Le skill sait **créer** un cours de zéro, **mettre en conformité** un dépôt existant, et **convertir** un article du site mkdocs.
8. Rien n'exige d'installation locale lourde : hyperion n'a ni Node, ni LaTeX, ni poppler.

---

## 3 — Non-objectifs

- **Les dépôts de TP ne sont pas concernés.** `bash-tp01-premiersScripts`, `sysadmin-linux-tp21-conso-fondamentaux` et leurs `-CORR` gardent leur forme actuelle, décrite par ailleurs (modèle `git-tp01-decouverte`). Un dépôt de cours cite son TP, il ne l'absorbe pas.
- **Pas d'index global.** La découverte passe par la progression dans `tracker`, qui porte les liens. Le kit ne génère pas de page listant les cours.
- **`sysadmin-linux-slides` n'est pas repris.** C'est un essai antérieur dont l'organisation agrégée contredit le principe d'un dépôt par bloc. Seul son thème `ciel.css` est conservé, tel quel.
- **Pas de migration en masse du site mkdocs.** La conversion d'un article est déclenchée article par article, à la demande.
- **Pas de dépôt `-CORR` pour les cours.** La version remplie est un PDF de la release.
- **Pas de refonte du thème des slides.** `ciel.css` est figé ; le travail de conception visuelle porte sur le papier.

---

## 4 — Anti-objectifs

Des situations qui signeraient l'échec même si tout « fonctionne » :

- **Un cours qui ne se régénère plus** parce que le kit a changé sans prévenir. Le couplage à un kit central est le risque principal de cette architecture ; il doit être versionné, et une mise à jour du kit ne doit jamais casser silencieusement trente dépôts.
- **Du gabarit visible par les étudiants.** Un `{{VERSION}}`, un marqueur de trou mal choisi ou un reste de syntaxe mkdocs affiché sur github.com discrédite le support.
- **Des fichiers générés versionnés.** `slides/output/` dans l'index, c'est des diffs illisibles et des conflits à chaque build.
- **Un cours qui exige LaTeX, Node ou une installation locale** pour être modifié. L'enseignant doit pouvoir corriger une faute depuis n'importe quelle machine, y compris l'interface web de GitHub.
- **Une couleur qui disparaît à l'impression.** Les documents sont lus en couleur et imprimés en noir et blanc : deux encadrés de clarté voisine deviennent le même gris.
- **Trente dépôts qui divergent** parce que la mise en conformité est trop coûteuse pour être relancée.
- **Un document papier qui ne laisse pas la place d'écrire**, ou qui déborde d'une page à l'autre au milieu d'un trou.

---

## 5 — Contraintes

### Machine de travail

hyperion est headless, piloté en SSH. Il dispose de **Docker** et de **uv**. Il n'a **ni Node, ni LaTeX, ni poppler, ni ImageMagick**, et on ne cherche pas à les y installer : tout outil local passe par Docker ou par `uv run --with`.

### GitHub

- Organisation `ciel-ir-rascol`, plan **enterprise** : la visibilité *internal* est disponible. `members_can_create_internal_repositories` est à `false` ; la création se fait donc en tant que propriétaire.
- Les **dépôts de cours sont publics** (les étudiants les consultent).
- Le **kit est internal**.
- **Première étape de l'implémentation, avant tout le reste :** vérifier qu'un dépôt public peut consommer une action composite hébergée dans un dépôt internal de la même organisation. Si ce n'est pas le cas, **le kit passe en public** : il ne contient que du thème, du CSS et des scripts, sous la même licence que les cours. On n'introduit pas de jeton d'organisation à renouveler.
- GitHub Pages par dépôt, source **GitHub Actions**, à activer une fois par dépôt dans les réglages.

### Outils de génération

- **Marp CLI v4.5.1** pour les slides (HTML et PDF), via l'image `marpteam/marp-cli:v4.5.1`. Chrome y est embarqué ; `CHROME_NO_SANDBOX=1` est nécessaire sur les runners Ubuntu.
- **WeasyPrint** pour le PDF du cours. Python, installable par pip, sans LaTeX. Il gère la pagination CSS : en-tête et pied de page récurrents, numérotation, sauts de page contrôlés, sommaire.
- Le convertisseur markdown doit gérer les **alertes GitHub** (`> [!NOTE]`, `> [!WARNING]`, `> [!TIP]`, `> [!IMPORTANT]`), qu'aucune bibliothèque ne connaît nativement.

### Licence

CC BY-NC-SA 4.0, mentionnée dans le `README.md` et dans le pied de page du document papier.

---

## 6 — Décisions prises

### 6.1 Nommage

`<séquence>-c<NN>-<séanceEnCamelCase>`

- `<séquence>` : le slug de la séquence, pas celui de la technologie du jour. Les scripts Bash appartiennent à la séquence Linux : `linux-c06-scriptsBash`.
- `<NN>` : le numéro du bloc dans la séquence, sur deux chiffres.
- `<séanceEnCamelCase>` : un mot ou deux, première lettre minuscule.

Exemples : `linux-c06-scriptsBash`, `git-c01-decouverte`, `cpp-c03-tableauxVecteurs`.

`git-cours01-decouverte` devient `git-c01-decouverte`. GitHub redirige l'ancien nom, mais **l'URL GitHub Pages change** : les liens déjà distribués aux étudiants et la progression `tracker` doivent être mis à jour.

### 6.2 Contenu d'un dépôt de cours

```text
linux-c06-scriptsBash/
├── README.md              présentation, déroulé, liens, licence
├── cours.yml              métadonnées du bloc
├── COURS.md               le cours — source unique du document papier
├── slides/
│   ├── 06-scripts-bash.md deck Marp
│   └── img/               SVG et images, partagés avec le cours
└── .github/workflows/
    ├── pages.yml          publication des slides sur Pages
    └── release.yml        génération des PDF sur tag
```

Pas de `themes/`, pas de `build.sh`, pas de `scripts/`, pas de `output/`, pas de `workspace_LaTex/`. Un `.vscode/settings.json` déclare le thème `ciel` par son URL dans le kit, pour l'aperçu Marp dans VS Code.

`cours.yml` porte ce que le cartouche et les en-têtes affichent : séquence, numéro de bloc, titre, durée, TP associé, capacités attendues, année. Sa structure exacte est laissée au constructeur.

### 6.3 Le kit central

`cielir-cours-kit`, internal, contient :

- `themes/ciel.css` — le thème Marp, repris **tel quel** de `git-cours01-decouverte` ;
- `themes/cours.css` — la feuille du document papier, à écrire ;
- le convertisseur markdown → HTML et son extension pour les alertes GitHub et les trous ;
- l'**action composite** que les dépôts de cours appellent ;
- la documentation du standard, dont ce document.

Consommation par une action composite épinglée sur un tag flottant :

```yaml
- uses: ciel-ir-rascol/cielir-cours-kit@v1
```

Le tag `v1` est déplacé après validation sur un dépôt réel. Une rupture de compatibilité passe à `v2`, et les dépôts migrent au rythme de leur propriétaire.

**Les versions du kit et celles des cours sont deux numérotations indépendantes** et ne se ressemblent que par hasard : `cielir-cours-kit@v1` est un tag flottant de compatibilité, `v1.02` sur un cours est une publication datée.

Un tag flottant rend le build non reproductible, ce qui frotte contre l'anti-objectif n° 1. On l'assume, encadré par trois règles :

- le kit porte un **dépôt témoin** — un cours jouet couvrant tous les éléments de mise en page — régénéré à chaque modification du kit ; le tag `v1` ne bouge que si le témoin se régénère sans régression ;
- la **version exacte du kit** utilisée (son SHA et son tag) est inscrite dans les notes de release de chaque cours, de sorte qu'une génération passée soit rejouable en épinglant ce SHA ;
- régénérer un ancien tag de cours utilise le kit **courant**, pas celui de l'époque. Les PDF déjà attachés à la release ne sont jamais réécrits : ils sont le livrable, le build n'est qu'un moyen de les produire.

**Pas de submodule git** : un submodule épingle un SHA, impose `--recursive`, se met en HEAD détachée, et demande un commit dans chaque dépôt pour avancer.

Pour une génération locale, une cible `make` récupère le kit dans un `.kit/` ignoré par git. Pour l'aperçu des slides dans VS Code, le thème est référencé par son URL : rien à installer.

### 6.4 Versions et releases

- **Schéma :** `vX.YY`. `X` est la mouture de la promotion (`v1` = 2026-2028, `v2` = la suivante). `YY`, sur deux chiffres, est la retouche en cours d'année : `v1.01` première publication, `v1.02` après correction de fautes, `v1.03` après ajout d'un exemple.
- **Un seul tag par dépôt** : le cours et les slides d'un bloc avancent ensemble.
- **Aucune version n'est écrite dans les sources.** Elle est injectée à la génération, au pied des slides et dans le cartouche du document papier. Les `.md` du dépôt n'en portent aucune trace, et il n'y a donc pas de script de version à maintenir : `git tag v1.02 && git push --tags` suffit.
- **Contenu d'une release :**

  | Fichier | Contenu |
  | --- | --- |
  | `slides.pdf` | le diaporama |
  | `cours.pdf` | le cours complet |
  | `cours-a-trous.pdf` | le même, à compléter |

- **GitHub Pages publie sur tag uniquement**, pas à chaque push sur `main` : ce que consulte un étudiant correspond toujours à une version publiée. Corriger une faute demande donc un tag — c'est précisément ce qu'est une `v1.02`.

### 6.5 Le document papier

Format retenu : la **fiche compacte**, sur le modèle de `C01_introCpp_fiche_a_trous.pdf` plutôt que du document d'accompagnement aéré de `git-cours01-decouverte`. Caractéristiques :

- en-tête sur une ligne, filet noir épais ;
- titres de partie en bandeau gris à filet latéral ;
- trous en pointillés ;
- tableaux et schémas à compléter ;
- deux pages pour une heure de cours, plutôt que cinq.

**En couleur.** Les étudiants consultent et impriment le PDF eux-mêmes ; l'impression de masse au lycée se fera en noir et blanc. Les teintes doivent donc rester distinguables en niveaux de gris : différence de **clarté**, pas seulement de teinte, et jamais la couleur comme seule porteuse d'information.

Le cartouche, les bandeaux, les encadrés, l'environnement « terminal » et la mise en page générale transposent `workspace_LaTex/macros.sty` (395 lignes, à lire avant d'écrire le CSS). Ce qui ne se transpose pas, c'est TikZ : les schémas deviennent des SVG.

L'interligne doit être plus large dans la version à trous que dans la version remplie — il faut la place d'écrire à la main — et un trou ne doit jamais être coupé par un saut de page.

**Polices.** `macros.sty` utilise `helvet` pour le texte et `zi4` (Inconsolata) pour les commandes. Le CSS reprend ce couple : une grotesque proche d'Helvetica et Inconsolata, toutes deux libres. Les fichiers de police sont **embarqués dans le kit**, pas installés sur le runner ni chargés depuis Google Fonts : c'est la seule façon d'obtenir le même PDF sur le runner, en Docker et en local.

**Ce qu'on vérifie avant de dire que `cours.css` est fini :**

- le PDF d'un bloc d'une heure tient en deux pages, trois au plus ;
- aucun trou, aucune ligne de réponse et aucun bandeau de partie n'est coupé par un saut de page ;
- converti en niveaux de gris, chaque type d'encadré reste distinguable des autres et le texte garde un contraste suffisant ;
- les polices sont embarquées dans le PDF ;
- le rendu est comparé visuellement à `C01_introCpp_fiche_a_trous.pdf`, qui fait référence.

### 6.6 Les trous

Marqués dans `COURS.md` par `<ins>réponse</ins>` : du HTML valide en markdown, que github.com affiche souligné, et qui porte le sens « à insérer ».

- Dans `cours.pdf`, le contenu de `<ins>` est rendu comme une réponse.
- Dans `cours-a-trous.pdf`, il devient une ligne vide, dont la largeur est calculée d'après la longueur de la réponse — comme le fait `\trou` aujourd'hui.

Le `**gras**` reste de l'emphase et ne devient jamais un trou : l'auteur n'a pas à choisir entre « mot important » et « mot à faire écrire ».

Il faut aussi un équivalent de `\lignes{n}` — plusieurs lignes pointillées pour une réponse rédigée, remplacées par la réponse dans la version complète. Sa syntaxe est laissée au constructeur.

Conséquence assumée : `COURS.md` est public et contient les réponses. Ce n'est pas un secret — le cours est fait pour être lu — mais c'est à savoir.

### 6.7 Les schémas

Un schéma est un **SVG unique**, rangé dans `slides/img/` et utilisé par les slides comme par le document papier. Plus de double entretien SVG + TikZ.

Pour un schéma à compléter, il faut une variante aux cases vides. La façon de la produire — second fichier, ou classes CSS masquant les étiquettes dans un SVG unique — est laissée au constructeur, avec une préférence pour la solution qui évite de maintenir deux fichiers.

### 6.8 Aucune information personnelle

Les dépôts sont publics. Y figurent la discipline, la classe, l'établissement (`Lycée Louis Rascol, Albi`) et la séquence. N'y figurent **jamais** : nom, prénom, adresse électronique, téléphone, signature, ni aucune donnée d'étudiant. La mise en conformité doit le vérifier.

Les crédits d'images (auteur, licence, source) restent obligatoires, sur le modèle du tableau de crédits de `git-cours01-decouverte`.

**Comment c'est vérifié.** Un contrôle du kit cherche dans les fichiers du dépôt une liste de motifs : adresse électronique, numéro de téléphone français, nom et prénom de l'enseignant. Il tourne dans le workflow de release et **bloque la publication**, parce qu'une fuite devient publique au moment où la release paraît.

Le contrôle ne porte **que sur les fichiers**, pas sur l'historique git : l'adresse de l'auteur des commits est inhérente à tout dépôt git et ne relève pas de ce standard. Aucune réécriture d'historique n'est prévue.

### 6.9 Les trois modes du skill

**Créer.** À partir d'une séquence, d'un numéro de bloc, d'un titre et d'une durée : création du dossier local, du dépôt distant, de la config et des workflows, puis **rédaction du cours** — `COURS.md` à la densité de la fiche, trous posés sur les notions qui doivent passer par la main de l'étudiant, deck Marp suivant le même plan, schémas en SVG. L'enseignant relit, corrige, tague.

**Mettre en conformité.** Sur un dépôt existant : renommage, conversion du `.tex` en `COURS.md` (les `\trou` deviennent des `<ins>`), abandon de `macros.sty`, retrait des fichiers générés de l'index, remplacement des workflows, vérification de l'absence d'information personnelle, premier tag. Le deck et le thème ne bougent pas.

La conversion du `.tex` n'est **pas** un script déterministe : `macros.sty` fait 395 lignes et contient du TikZ, des `tcolorbox`, des tableaux et des flottants. C'est une réécriture faite par le modèle, relue par l'enseignant. Deux règles la cadrent : devant une construction qu'il ne sait pas transposer, le skill **s'arrête et demande** — il ne laisse jamais de marqueur ni de syntaxe brute dans le `COURS.md` ; et les schémas TikZ sont **redessinés en SVG par le skill**, puis validés visuellement.

**Convertir un article du site.** À partir d'un fichier de `ciel-ir-rascol.github.io/docs/` : les admonitions mkdocs (`!!! tip`, `!!! warning`) deviennent des alertes GitHub, le texte est resserré à la densité fiche, les trous sont posés, un deck est déduit du plan.

Les articles ne se ressemblent pas, et le mode doit traiter deux formes :

- **l'article rédigé**, comme `docs/linux/05-Scripts_bash.md` : de la prose, longue — 1 574 lignes — qui ne tient pas dans un seul bloc. Le skill **propose un découpage en blocs et le fait valider avant d'écrire**. C'est une supposition de conception, pas une demande explicite de l'enseignant ;
- **l'article qui n'est qu'un lien vers un diaporama**, comme `docs/cpp/04-tableauxVecteurs/` : la page fait deux lignes et renvoie à `slides-tableauxVecteurs.md`, un deck Marp de 338 lignes. Il n'existe aucun cours rédigé. Le skill **écrit le `COURS.md` à partir du deck**, puis reprend le deck au thème `ciel`.

Ces vieux decks apportent leur lot de travail de reprise, qu'il faut prévoir : ils portent leur propre style en ligne au lieu du thème `ciel`, une ligne de version écrite à la main (`Release : v1.0 (23.09.23)`), parfois un en-tête resté d'un autre cours, un renvoi vers un dépôt qui n'existe plus, et **l'adresse électronique de l'enseignant sur la page de titre** — exactement ce que le contrôle du § 6.8 doit attraper. Leurs schémas SVG, eux, sont récupérables tels quels.

### 6.10 Où vit le skill

Dans un dépôt dédié `~/repos/claude-skills`, versionné, contenant `skills/`, `commands/`, le `settings.json` partageable et un `install.sh` qui pose les liens symboliques vers `~/.claude/`. Il accueille `infra-cielir`, qui existe déjà, et `cours-cielir`.

`~/.claude` lui-même n'est **pas** versionné : il contient les transcriptions de conversations, la mémoire, les caches de plugins et `settings.local.json`.

Le skill nomme la version du kit qu'il attend. Ce dépôt est créé au moment de l'implémentation, pas avant.

---

## 7 — Laissé au constructeur

- Le choix de la bibliothèque markdown Python (`markdown-it-py` avec extensions, ou `python-markdown`), et la forme de l'extension qui traite les alertes GitHub, `<ins>` et les lignes de réponse.
- La structure exacte de `cours.yml`.
- Le calcul de la largeur d'un trou à partir de la longueur de la réponse, en CSS.
- La syntaxe de l'équivalent de `\lignes{n}`.
- La forme exacte de l'action composite et le découpage entre `pages.yml` et `release.yml`.
- Le gabarit du `README.md` d'un dépôt de cours — en s'inspirant de celui de `git-cours01-decouverte`, qui est bon : déroulé minuté, arborescence, crédits, licence.
- La production de la variante « à compléter » d'un schéma SVG.
- La coloration syntaxique des blocs de code dans le PDF, et son rendu en niveaux de gris.

---

## 8 — Périmètre de la première livraison

Trois jalons, dans cet ordre. Chacun valide un mode du skill.

**Jalon 0 — le test d'accès.** Un dépôt public consomme-t-il une action composite d'un dépôt internal ? Si non, le kit passe en public. Rien d'autre n'est écrit avant d'avoir la réponse.

**Jalon 1 — le kit, validé sur un cours jouet.** Thème, `cours.css`, convertisseur, contrôle d'information personnelle, action composite, workflows. Le cours jouet sert de **dépôt témoin** permanent (§ 6.3) : il couvre tous les éléments de mise en page — trous, lignes de réponse, encadrés, terminal, tableaux, schéma SVG, code coloré — et c'est lui qui autorise le déplacement du tag `v1`. Il valide le mode **Créer**.

**Jalon 2 — `git-cours01-decouverte` → `git-c01-decouverte`.** Le premier vrai dépôt : renommage, conversion du `.tex`, suppression de `workspace_LaTex/` et de `slides/output/`, premier tag `v1.01`. Il valide le mode **Mettre en conformité**, et c'est lui qui éprouve pour de bon l'accès au kit et la chaîne de release. Comprend la reprise de l'URL GitHub Pages dans la progression `tracker` et partout où l'ancienne a été distribuée.

**Jalon 3 — `cpp-c04-tableauxVecteurs`.** Converti depuis `ciel-ir-rascol.github.io/docs/cpp/04-tableauxVecteurs/`, c'est-à-dire en pratique depuis son deck Marp, faute de cours rédigé. Il valide le mode **Convertir**, sur la forme la plus difficile des deux. Sujet choisi par l'enseignant de préférence aux scripts Bash, jugés trop denses pour un premier essai.

---

## 9 — Références à lire avant d'implémenter

| Chemin | Ce qu'on y trouve |
| --- | --- |
| `cielir/git-cours01-decouverte/` | l'ébauche du standard : slides, workflow, README |
| `.../slides/themes/ciel.css` | le thème Marp, à reprendre tel quel |
| `.../workspace_LaTex/macros.sty` | le vocabulaire typographique à transposer en CSS |
| `.../workspace_LaTex/output/Cours01_Git_Decouverte.pdf` | le format aéré, **écarté** |
| `~/transfert/C01_introCpp_fiche_a_trous.pdf` | le format compact, **retenu** |
| `cielir/ciel-ir-rascol.github.io/docs/` | les articles à convertir |
| `.../docs/cpp/04-tableauxVecteurs/` | le sujet du jalon 3 : un deck Marp, pas un cours rédigé |
| `cielir/sysadmin-linux-tp21-conso-fondamentaux/` | le standard des TP, pour les renvois |
