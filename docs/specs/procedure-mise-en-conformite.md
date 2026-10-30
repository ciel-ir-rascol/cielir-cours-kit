# Procédure : mettre un dépôt de cours existant en conformité

Tirée de la première mise en conformité réelle : `git-cours01-decouverte` devenu `git-c01-decouverte` (cours Marp + fiche LaTeX à trous). À suivre dans l'ordre. Chaque étape dit quoi faire, puis ce qui a mordu.

Prérequis : le kit à jour (`/home/joris/repos/cielir/cielir-cours-kit`), `gh` connecté, Docker pour Marp. Les commandes du kit se lancent **depuis le kit** (`uv run cielir-cours …`, `make temoin DEPOT=../<depot>`).

## 0. Cadrer avant de toucher

Décisions déjà prises, à ne pas rediscuter :

- pas de fichier `LICENSE` dans un dépôt de cours ; la licence est nommée dans le README ;
- le README vient de `gabarits/README.md`, rempli à la main ;
- plus de dépôt `-CORR` pour un cours : la version remplie est `cours.pdf` dans la release ;
- publication sur tag uniquement ; l'ancien workflow de publication sur `main` disparaît ;
- l'ancien contenu reste dans l'historique git : on supprime sans archiver.

Lire la source LaTeX en entier **avant** de convertir, pour dresser deux listes : (a) les macros utilisées, (b) les figures TikZ. Comparer ensuite aux possibilités du kit (README du kit, §« Écrire un cours ») : tout ce qui n'est pas dans la table de la §3 est à trancher *avant* d'écrire, pas pendant.

Se donner une référence de comparaison : le PDF LaTeX d'origine (`workspace_LaTex/output/*.pdf`) et le PDF des slides d'origine, à garder hors du dépôt (dans un dossier temporaire).

## 1. Renommer et réorganiser

### 1.1 Le nom

Le nom se déduit de `cours.yml` : `{sequence}-c{bloc:02d}-{slug}` (`git`, `1`, `decouverte` donne `git-c01-decouverte`). Slug en camelCase, sans tiret.

```bash
gh repo rename git-c01-decouverte --repo ciel-ir-rascol/git-cours01-decouverte --yes
cd <dossier du dépôt> && git remote set-url origin https://github.com/ciel-ir-rascol/git-c01-decouverte.git
mv git-cours01-decouverte git-c01-decouverte    # le dossier local aussi
```

Pièges :

- `gh repo rename` demande confirmation : ajouter `--yes` en non interactif.
- GitHub redirige l'ancien nom (git, web, API) mais **pas l'URL GitHub Pages** : l'ancienne adresse des slides meurt. Voir §6.
- Renommer aussi le dossier local ; le `make temoin DEPOT=../<nom>` des instructions suppose le nom final. Les scripts ou signets qui pointent sur l'ancien chemin cassent.
- Les **paramètres du dépôt survivent au renommage**, Pages et environnements compris (voir §4.2).

### 1.2 Les fichiers

```bash
git rm -r build.sh .github/workflows/pages.yml slides/themes slides/output workspace_LaTex \
          .vscode/run_docker.sh .vscode/extensions.json
git mv slides/01-<ancien>.md slides/01-decouverte.md      # convention NN-slug
cp <kit>/gabarits/publier.yml  .github/workflows/publier.yml    # copie TELLE QUELLE
cp <kit>/gabarits/settings.json .vscode/settings.json
cp ../cielir-cours-temoin/.gitignore .gitignore      # une seule ligne utile : build/
```

Avant de supprimer `workspace_LaTex/`, **copier le `.tex` et les PDF d'origine hors du dépôt** : on en a besoin pour la §3. Ne pas utiliser `git rm --cached` pour « garder une copie » : on se retrouve avec un dossier non suivi qui traîne.

Ce qu'on garde : le deck Marp (`slides/NN-*.md`) et `slides/img/`. Le thème n'est plus copié dans le dépôt : `settings.json` le prend à l'URL du kit (`…/cielir-cours-kit/v1/themes/ciel.css`). Vérifier que le thème supprimé était bien identique à `themes/ciel.css` du kit (`diff`), sinon le deck change d'aspect : ici ils étaient identiques.

`.vscode/extensions.json` (recommandation de l'extension Marp) n'existe pas dans le standard : il disparaît, le README du gabarit dit d'installer l'extension. `run_docker.sh` ne servait qu'à LaTeX.

### 1.3 `cours.yml`

Champs exacts de la dataclasse `Cours` (`src/cielircours/config.py`) : `sequence`, `bloc`, `slug`, `titre`, `discipline`, `classe`, `etablissement`, `duree`, `tp`, `capacites`.

```yaml
sequence: git
bloc: 1
slug: decouverte
titre: Découverte de Git et GitHub
discipline: Informatique
classe: BTS CIEL-IR 1ère année
etablissement: Lycée Louis Rascol, Albi
duree: 1 h
tp: git-tp01-decouverte
capacites:
  - …            # reprises de \capacites{} du .tex, sans le LaTeX
```

Les capacités du `.tex` (`\capacites{\item …}`) deviennent cette liste : le gabarit HTML du kit les affiche en tête de fiche, **ne pas les recopier dans `COURS.md`**. Sans le LaTeX : `$\rightarrow$` devient `→`, `\texttt{git add}` devient `git add`.

La version et la date (`\version{}`, `\dateversion{}`) **ne vont nulle part** : elles sont injectées à la génération.

## 2. README

Copier `gabarits/README.md`, remplacer tout ce qui est entre « … », supprimer le commentaire d'en-tête. Reprendre de l'ancien README : déroulé, capacités, crédits d'images (tableau complet, avec la mention de marque déposée le cas échéant). Retirer : la phrase sur le dépôt `-CORR`, la section sur la compilation LaTeX et Docker, la table des macros, la mention de `build.sh`, tout nom d'enseignant ou courriel, toute version et toute date.

Ligne « Schémas » du tableau des crédits : garder « hors logos » si `slides/img/` contient des logos, ceux-ci ayant leur propre ligne.

## 3. Convertir le `.tex` en `COURS.md`

Table de conversion, telle qu'appliquée :

| LaTeX | Markdown |
| --- | --- |
| `\trou{x}`, `\trou[coef]{x}` | `<ins>x</ins>` (le coefficient disparaît : la longueur est calculée par le kit) |
| `\lignes{n}{x}` | bloc `:::reponse n` … `:::` contenant `x` |
| `\rappel`, `\astuce`, `\important` | alerte `> [!NOTE]`, `> [!TIP]`, `> [!IMPORTANT]` ; `\important{Danger}` : `> [!CAUTION]` |
| `\partie{titre}` | `## titre` (la numérotation est automatique : ne pas numéroter) |
| `\exercice{titre}` | `### Exercice : titre` |
| `\textbf{}`, `\textit{}`, `\texttt{}` | `**` `**`, `*` `*`, backticks |
| `\begin{itemize}`, `multicols` | liste markdown (une colonne) |
| `tabular` | tableau markdown ; la ligne d'en-tête reçoit `\rowcolor` → inutile |
| `\includegraphics` + `\credit` | `<img … style="…">` + ligne de crédit en italique |
| `\begin{tikzpicture}` | SVG redessiné, voir §3.3 |
| `\begin{terminal}` | bloc ```` ```terminal ````, **sauf s'il contient un trou**, voir §3.2 |
| `\capacites`, `\licence`, `\maketitle`, `\introduction` | `cours.yml` / pied de page du kit / cartouche du kit / premier paragraphe |

Exemples de transcription littérale : `$\neq$` → `≠`, `$=$` → `=`, `\dots` → `…`, `\textasciitilde` → `~`, `\_` → `_`, `\#` → `#`.

Les macros de mise en page pure (`\needspace`, `\vfill`, `\medskip`, `\hfill`, `\linespread`, `\thispagestyle`) n'ont pas d'équivalent et ne sont pas à reproduire : la pagination est celle du kit.

Les chemins d'image sont relatifs à la racine du dépôt : `slides/img/x.jpg`. Les images du LaTeX (`workspace_LaTex/img/`) étaient des doublons de `slides/img/` : on réutilise celles de `slides/`.

### 3.1 Ce que le kit refuse, et ce qui ne se voit pas

- Un `<ins>` qui reste dans la sortie (non apparié, imbriqué, sur plusieurs paragraphes, dans un titre de lien) **arrête la génération**. C'est voulu : un trou mal formé laisserait la réponse en clair.
- Une réponse ne peut pas être répartie sur deux paragraphes : un trou = une réponse sur une ligne ; plus long, c'est un `:::reponse`.
- Un `:::reponse` ne se combine pas bien avec une liste numérotée (le bloc coupe la liste, et la numérotation recommence à 1) : écrire les questions en paragraphes `**1.** …`.
- Les `<ins>` dans une cellule d'en-tête de tableau fonctionnent. Un en-tête de tableau vide (`| | | |`) produit une barre vide en haut du tableau : mettre quelque chose dans l'en-tête.

### 3.2 Un trou dans un bloc `terminal` : le cas qui ne passe pas

Le contenu d'un bloc de code n'est jamais interprété : un `<ins>` y reste littéral, la réponse n'est pas cachée et la syntaxe apparaît brute. Le `terminal` LaTeX acceptait des `\trou`, pas le kit. Quand un terminal contient un trou, ne **pas** utiliser un bloc de code. Solution appliquée : une ligne de code en ligne par ligne de terminal, les trous entre deux spans, des sauts de ligne par `\` en fin de ligne.

```markdown
`git config --global user.name "`<ins>Prénom Nom</ins>`"`\
`git config --global init.defaultBranch main`
```

Les commentaires `# …` sont des spans de code. Conséquence : ces lignes n'ont pas le fond gris du bloc terminal mais celui du code en ligne, et les alignements `\hfill` du LaTeX sont perdus. Un terminal **sans** trou reste un vrai bloc `terminal`.

C'est un manque du kit (trous dans un bloc terminal). À arbitrer : soit le kit apprend à les traiter, soit on garde ce contournement.

### 3.3 Schémas TikZ

Un schéma TikZ à trous se redessine en SVG, **dans un fichier distinct** de celui des slides s'il en existe déjà un : celui des slides montre les réponses.

Règles du SVG remplissable (voir le témoin, `slides/img/schema.svg`) :

- tout élément qui est une réponse porte `class="remplissable"` (texte rouge `#be1e2d`, gras) ;
- sous chaque réponse, un trait pointillé (`.ecrire`) **non** remplissable : c'est la ligne où écrire, il reste dans la version à trous ;
- fonds clairs, traits noirs : lisible en niveaux de gris ;
- le kit retire les éléments `.remplissable` de l'arbre, il ne les masque pas.

Piège de mesure : sans la police finale, on ne sait pas la largeur d'un texte. Positionner les mots avec `text-anchor="middle"` autour de traits de largeur généreuse, plutôt que d'enchaîner des textes à la suite en comptant des caractères.

Ici : `chaine-git.svg` (slides, sans trous) est resté tel quel ; `chaine-git-a-completer.svg` en est dérivé pour la fiche (fonds clairs partout, 9 étiquettes remplissables).

### 3.4 Pièges de contenu à surveiller

- **Vrai/faux** : l'original faisait entourer « V » ou « F » (version corrigée : la réponse en rouge). Converti en tableau *Affirmation / Vrai ou faux ?* avec `<ins>vrai</ins>` ou `<ins>faux</ins>`. Le geste de l'étudiant change (écrire au lieu d'entourer) ; c'est signalé à l'enseignant.
- **Photos** : le LaTeX les recadrait en carré/portrait ; en HTML, `object-fit: cover` avec largeur et hauteur fixes reproduit le recadrage (`object-position` pour décaler). Un `float:right` dans un `<span>` pose la photo à côté du texte (équivalent de `wrapfigure`). La mention de licence se glisse sous la photo, pas seulement en fin de document.
- **Photos en tableau** : les noms à compléter sont mis en en-tête de colonne, au-dessus des photos.
- **Rien d'inventé** : une conversion ne doit pas ajouter de texte absent du `.tex`. Les titres de `\rappel{…}{…}` (par exemple « Git ≠ GitHub : complétez le tableau ») n'ont pas leur place dans une alerte (titre fixe) : ils deviennent un `###` placé juste avant le tableau.
- **Divergences deck / fiche** : en convertissant, on lit les deux sources côte à côte. Ici : « premier commit le 7 avril 2005 » dans la fiche contre « commence Git le 3 avril 2005 » dans le deck. Les deux sont défendables (début du développement, premier commit) ; c'est à l'enseignant de dire s'il les aligne. Ne pas trancher à sa place.

## 4. Vérifier avant de publier

### 4.1 Contrôle de confidentialité

```bash
cd <kit> && uv run cielir-cours verifier ../git-c01-decouverte
```

Il passe sur **tous** les fichiers texte, deck compris. Ici il a refusé deux lignes du deck : `adresse@du-compte-github.fr` (exemple de configuration `user.email` et de `ssh-keygen -C`). Trois réponses possibles :

1. changer l'exemple : `adresse du compte GitHub` (retenu : c'est aussi ce que dit la fiche) ;
2. un domaine réservé RFC 2606 (`prenom.nom@example.org`), que le contrôle accepte ;
3. `.cielir-ignore` : **à éviter ici**, il exclut le fichier entier (le deck complet, donc plus aucun contrôle sur lui), il n'ignore pas une ligne.

Une modification du deck pour passer le contrôle est une modification du cours : la signaler.

### 4.2 Génération

```bash
cd <kit> && make temoin DEPOT=../git-c01-decouverte
# produit build/git-c01-decouverte/{cours.pdf,cours-a-trous.pdf,slides.pdf}
```

`make` enchaîne `verifier`, les deux PDF de la fiche et les slides (Marp dans Docker). Hors du dépôt : rien n'est écrit dans le dépôt de cours.

### 4.3 Relecture : à faire vraiment, avec les yeux

L'outil de rendu PNG n'est pas dans l'environnement du kit : `uv run --with pymupdf python script.py` (pymupdf s'installe à la volée).

```python
import sys, pymupdf
pdf, sortie, dpi = sys.argv[1], sys.argv[2], int(sys.argv[3])
gris = len(sys.argv) > 4
for i, page in enumerate(pymupdf.open(pdf)):
    page.get_pixmap(dpi=dpi, colorspace=pymupdf.csGRAY if gris else pymupdf.csRGB).save(f"{sortie}_p{i+1}.png")
```

Contrôles, dans cet ordre :

1. **Chaque page de `cours.pdf` et de `cours-a-trous.pdf`, à 75 dpi**, comparées à celles du PDF LaTeX d'origine : chaque trou, chaque tableau, chaque encadré, chaque photo, chaque exercice y est-il ?
2. **Fuite de réponses** dans le PDF à trous, par script : extraire les textes des `<ins>` du `COURS.md`, chercher dans le texte du PDF à trous ceux de 5 caractères et plus qui n'existent pas dans le texte fixe ; chercher aussi les étiquettes des SVG (qui doivent être à 0 occurrence si elles ne figurent pas ailleurs dans le texte).
3. **Niveaux de gris** (`csGRAY`) : les encadrés et les réponses se distinguent-ils sans couleur ?
4. **Slides** : même nombre de pages que l'original ; comparer le texte page à page avec le PDF d'origine en ignorant le pied de page (la version y est injectée). Seules les modifications voulues doivent ressortir.
5. **Pagination** : pas de dernière page ne contenant que le pied de licence ; ici la fiche tenait sur 4 pages (complet) et 5 (à trous), après avoir resserré les crédits.

À savoir : la version à trous est plus longue que la version complète (interligne 1,7). Une dernière page orpheline apparaît dans l'une et pas dans l'autre.

## 5. Publier

### 5.1 Commiter et pousser `main`

Des commits séparés : (1) structure (cours.yml, workflow, suppressions, renommage du deck), (2) `COURS.md` et schéma, (3) README. `git push origin main`. Pas de `--force`.

### 5.2 Régler Pages, une fois le dépôt renommé

```bash
gh api -X POST repos/ciel-ir-rascol/git-c01-decouverte/pages -f build_type=workflow
gh api -X POST repos/ciel-ir-rascol/git-c01-decouverte/environments/github-pages/deployment-branch-policies \
   -f name='v*' -f type=tag
```

Dans cet ordre : le second n'est possible qu'après le premier, qui crée l'environnement `github-pages`. Sans le second, le job `pages` du workflow est **refusé** : la politique par défaut n'autorise que `main`, or le workflow tourne sur un tag.

Pièges :

- Si le dépôt avait déjà Pages (c'est le cas d'un dépôt qui publiait ses slides), le premier appel répond **409 « already enabled »** : ce n'est pas une erreur. Les réglages survivent au renommage. Vérifier : `gh api repos/…/pages --jq '{build_type,html_url}'` doit donner `workflow`.
- L'ancien environnement garde sa politique `main` (liste de politiques : `main` et `v*`). Elle est inoffensive, on peut la laisser.
- L'URL Pages est celle du **nouveau** nom : `https://ciel-ir-rascol.github.io/git-c01-decouverte/`.

### 5.3 Poser le tag : le geste qui rend quelque chose de public

```bash
git tag v1.01 && git push origin v1.01
gh run watch
```

Un tag mal formé est refusé par le workflow avec le format attendu (`vN.NN`). Attendu : trois jobs verts, une release `v1.01` avec `slides.pdf`, `cours.pdf`, `cours-a-trous.pdf`, les slides en ligne.

Le tag est **la dernière étape**, à ne poser qu'après relecture humaine des trois PDF. Une release publiée se retire (suppression de la release et du tag), mais les slides en ligne restent diffusées d'ici là.

## 6. Après la publication

- Remplacer l'ancienne URL Pages (`…/git-cours01-decouverte/`) par la nouvelle partout où elle a été diffusée : progression `tracker`, supports, courriels, README du TP (`git-tp01-decouverte`).
- Les dépôts `-CORR` de l'ancien schéma : le correctif de la fiche est désormais `cours.pdf` de la release. Ici `git-cours01-decouverte-CORR` n'a pas été touché (dépôt hors périmètre) ; à archiver ou supprimer par l'enseignant, une fois `v1.01` vérifiée.

## Résumé : ordre d'exécution

1. `gh repo rename` + dossier local + `remote set-url`
2. copier `.tex` et PDF d'origine hors du dépôt, puis `git rm` de l'outillage ; `cours.yml`, `publier.yml`, `settings.json`, `.gitignore`
3. convertir en `COURS.md` ; SVG remplissables
4. README du gabarit
5. `verifier`, `make temoin`, relecture des PDF (y compris fuite et niveaux de gris)
6. commits, `push origin main`
7. régler Pages et la politique de déploiement sur `v*`
8. **relecture humaine**, puis le tag, `gh run watch`
9. diffuser la nouvelle URL
