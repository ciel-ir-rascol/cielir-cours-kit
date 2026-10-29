# Kit de cours CIEL-IR — plan d'implémentation

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produire `cielir-cours-kit` — thème, feuille papier, convertisseur markdown et action GitHub — puis le skill `cours-cielir`, et s'en servir pour publier deux vrais cours.

**Architecture :** un paquet Python `cielircours` convertit `COURS.md` en deux PDF (complet et à trous) par markdown-it-py puis WeasyPrint ; les slides restent produites par Marp CLI en conteneur, la version étant injectée dans une copie temporaire du deck. Une action composite enchaîne les deux et attache les PDF à la release. Les dépôts de cours n'embarquent que du contenu.

**Tech Stack :** Python 3.12 (uv), markdown-it-py + mdit-py-plugins, WeasyPrint, pytest, pypdf (tests), Docker `marpteam/marp-cli:v4.5.1`, GitHub Actions.

**Spec :** `docs/specs/2026-10-29-cours-cielir-conception.md`

## Global Constraints

- Nom d'un dépôt de cours : `^[a-z0-9]+-c\d{2}-[a-z][A-Za-z0-9]*$` — `cpp-c04-tableauxVecteurs`.
- Numéro de version d'un cours : `^v\d+\.\d{2}$` — `v1.01`. Jamais écrite dans les sources, toujours injectée à la génération.
- Version affichée au format `v1.02 du 29.10.26` (cartouche papier et pied des slides), identique à celui de `macros.sty`.
- Release d'un tag = exactement `slides.pdf`, `cours.pdf`, `cours-a-trous.pdf`.
- GitHub Pages publie **sur tag uniquement**, jamais sur push.
- Aucun fichier généré n'est versionné dans un dépôt de cours.
- Aucune information personnelle enseignante dans un dépôt de cours ; le contrôle bloque la release.
- Polices embarquées dans le kit, jamais chargées depuis un CDN.
- Marp CLI est épinglé à `v4.5.1`, `CHROME_NO_SANDBOX=1`.
- `themes/ciel.css` est repris de `git-cours01-decouverte` **sans aucune modification**.
- Licence CC BY-NC-SA 4.0.
- hyperion n'a ni Node ni LaTeX : tout outil local passe par Docker ou `uv run`.
- Un PDF de bloc d'une heure tient en deux pages, trois au plus.

## Review Focus

Cinq cas que la conception implique sans les nommer ; chacun a son test dans la tâche qui en porte le code.

1. **Un `COURS.md` sans aucun trou** (cours purement expositif) : `cours-a-trous.pdf` doit être produit normalement, pas échouer ni être vide. → Tâche 5.
2. **Une réponse de trou longue** (une phrase entière) : la largeur calculée ne doit pas déborder de la colonne ni pousser le texte hors de la page. → Tâche 6.
3. **Un titre contenant `&`, `<` ou une apostrophe typographique** dans `cours.yml` : il arrive tel quel dans le cartouche HTML, donc doit être échappé. → Tâche 5.
4. **Un tag malformé** (`v1.2`, `1.01`, `v1.01-rc`) poussé par erreur : le workflow s'arrête avec un message clair au lieu de publier une release bancale. → Tâche 10.
5. **Une image référencée mais absente du dépôt** : WeasyPrint rend sans broncher un PDF amputé ; la génération doit échouer. → Tâche 5.

---

## Structure des fichiers

```text
cielir-cours-kit/
├── action.yml                       action composite consommée par les dépôts de cours
├── pyproject.toml                   paquet « cielircours », entrée console « cielir-cours »
├── Makefile                         cibles locales (Docker / uv)
├── motifs.yml                       motifs du contrôle d'information personnelle
├── src/cielircours/
│   ├── config.py                    lecture et validation de cours.yml
│   ├── mdtext.py                    markdown-it configuré selon le mode
│   ├── plugins/alertes.py           > [!NOTE] -> <aside class="alerte …">
│   ├── plugins/trous.py             <ins>…</ins> -> trou ou réponse
│   ├── plugins/lignes.py            :::reponse n -> lignes à écrire ou réponse
│   ├── rendu.py                     gabarit HTML + cartouche + WeasyPrint
│   ├── deck.py                      injection de la version dans une copie du deck Marp
│   ├── confidentialite.py           contrôle des motifs interdits
│   └── cli.py                       sous-commandes pdf / deck / verifier
├── gabarits/cours.html.j2           squelette du document papier
├── themes/ciel.css                  thème Marp, copie conforme
├── themes/cours.css                 feuille du document papier
├── themes/polices/*.woff2           polices embarquées
├── temoin/                          cours jouet : dépôt témoin permanent
└── tests/
```

Un dépôt de cours, lui, ne contient que `README.md`, `cours.yml`, `COURS.md`, `slides/`, `.vscode/settings.json` et `.github/workflows/publier.yml`.

**Écart assumé au document de conception.** Le § 6.2 annonce deux workflows, `pages.yml` et `release.yml`. Ils se déclenchent sur le même évènement et régénéreraient tout deux fois : ils sont remplacés par un seul `publier.yml` à trois jobs — `construire`, `pages`, `release`.

---

## Task 1 : Verdict sur l'action internal

**Files:**
- Create: `docs/specs/verdict-visibilite.md`

**Interfaces:**
- Produces : la visibilité définitive du kit, dont dépend la forme de `action.yml` (tâche 10).

- [ ] **Step 1 : Créer le kit sur GitHub en internal**

```bash
cd /home/joris/repos/cielir/cielir-cours-kit
gh repo create ciel-ir-rascol/cielir-cours-kit --internal --source=. --remote=origin
```

- [ ] **Step 2 : Poser une action composite minimale et un dépôt public d'essai**

`action.yml` à la racine du kit, avec un seul `run: echo ok`. Puis un dépôt public jetable `ciel-ir-rascol/essai-action-internal` dont le workflow fait `uses: ciel-ir-rascol/cielir-cours-kit@main`.

- [ ] **Step 3 : Déclencher et lire le résultat**

Run : `gh workflow run --repo ciel-ir-rascol/essai-action-internal essai.yml && gh run watch --repo ciel-ir-rascol/essai-action-internal`
Attendu : succès, ou échec de résolution de l'action.

- [ ] **Step 4 : Trancher et consigner**

En cas d'échec : `gh repo edit ciel-ir-rascol/cielir-cours-kit --visibility public --accept-visibility-change-consequences`. Écrire dans `docs/specs/verdict-visibilite.md` la commande, la sortie et la visibilité retenue. Supprimer le dépôt d'essai.

- [ ] **Step 5 : Commit**

```bash
git add docs/ action.yml && git commit -m "docs: verdict sur la visibilité du kit"
```

---

## Task 2 : Paquet et lecture de `cours.yml`

**Files:**
- Create: `pyproject.toml`, `src/cielircours/__init__.py`, `src/cielircours/config.py`
- Test: `tests/test_config.py`

**Interfaces:**
- Produces :
  - `class ConfigInvalide(ValueError)`
  - `@dataclass(frozen=True) class Cours` — champs `sequence: str`, `bloc: int`, `slug: str`, `titre: str`, `discipline: str`, `classe: str`, `etablissement: str`, `duree: str`, `tp: str | None`, `capacites: list[str]` ; propriété `depot: str`
  - `def lire_config(chemin: Path) -> Cours`

- [ ] **Step 1 : Écrire les tests qui échouent**

```python
def test_depot_compose_le_nom_normalise():
    c = lire_config(Path("tests/data/cours-cpp.yml"))
    assert c.depot == "cpp-c04-tableauxVecteurs"

def test_bloc_est_sur_deux_chiffres():
    assert lire_config(Path("tests/data/cours-bloc1.yml")).depot.startswith("git-c01-")

@pytest.mark.parametrize("fichier", ["slug-majuscule.yml", "bloc-zero.yml", "sans-titre.yml"])
def test_config_invalide_leve(fichier):
    with pytest.raises(ConfigInvalide):
        lire_config(Path("tests/data") / fichier)
```

Les fichiers de `tests/data/` sont à créer dans cette étape. `cours-cpp.yml` porte `sequence: cpp`, `bloc: 4`, `slug: tableauxVecteurs`.

- [ ] **Step 2 : Vérifier l'échec**

Run : `uv run pytest tests/test_config.py -v`
Attendu : FAIL, `ModuleNotFoundError: cielircours`

- [ ] **Step 3 : Implémenter**

`pyproject.toml` déclare le paquet, Python ≥ 3.12, les dépendances `markdown-it-py`, `mdit-py-plugins`, `weasyprint`, `jinja2`, `pyyaml`, et l'entrée console `cielir-cours = cielircours.cli:main`. `lire_config` valide : `bloc` entre 1 et 99, `slug` conforme à `^[a-z][A-Za-z0-9]*$`, `sequence` conforme à `^[a-z0-9]+$`, champs obligatoires présents. `depot` renvoie `f"{sequence}-c{bloc:02d}-{slug}"`.

- [ ] **Step 4 : Vérifier le succès**

Run : `uv run pytest tests/test_config.py -v` → PASS

- [ ] **Step 5 : Commit**

```bash
git add pyproject.toml src tests && git commit -m "feat: lecture et validation de cours.yml"
```

---

## Task 3 : Alertes GitHub

**Files:**
- Create: `src/cielircours/plugins/alertes.py`
- Test: `tests/test_alertes.py`

**Interfaces:**
- Produces : `def alertes_plugin(md: MarkdownIt) -> None`

Correspondance figée : `NOTE`→« Note », `TIP`→« Astuce », `IMPORTANT`→« Important », `WARNING`→« Attention », `CAUTION`→« Danger ».

`rendre(source)` est un utilitaire local du fichier de test : un `MarkdownIt("commonmark")` sur lequel seul `alertes_plugin` est appliqué.

- [ ] **Step 1 : Écrire les tests qui échouent**

```python
def test_note_devient_un_aside_titre():
    html = rendre("> [!NOTE]\n> Verrouiller plutôt que supprimer.")
    assert '<aside class="alerte alerte--note">' in html
    assert '<p class="alerte__titre">Note</p>' in html
    assert "Verrouiller plutôt que supprimer." in html

def test_citation_ordinaire_reste_un_blockquote():
    assert "<blockquote>" in rendre("> Une citation simple.")

def test_type_inconnu_reste_un_blockquote():
    assert "<blockquote>" in rendre("> [!TRUC]\n> x")
```

- [ ] **Step 2 : Vérifier l'échec** — Run : `uv run pytest tests/test_alertes.py -v` → FAIL

- [ ] **Step 3 : Implémenter**

Règle `core` après `block` : pour chaque `blockquote_open`, si le premier paragraphe commence par `[!TYPE]` connu, remplacer les jetons d'ouverture et de fermeture par du HTML brut et retirer le marqueur du texte.

- [ ] **Step 4 : Vérifier le succès** — Run : `uv run pytest tests/test_alertes.py -v` → PASS

- [ ] **Step 5 : Commit**

```bash
git add src/cielircours/plugins/alertes.py tests/test_alertes.py
git commit -m "feat: alertes GitHub converties en encadrés"
```

---

## Task 4 : Trous et lignes de réponse

**Files:**
- Create: `src/cielircours/plugins/trous.py`, `src/cielircours/plugins/lignes.py`, `src/cielircours/mdtext.py`
- Test: `tests/test_trous.py`, `tests/test_lignes.py`

**Interfaces:**
- Consumes : `alertes_plugin` (tâche 3)
- Produces :
  - `class Mode(StrEnum): COMPLET = "complet"; TROUS = "trous"`
  - `def trous_plugin(md: MarkdownIt, mode: Mode) -> None`
  - `def lignes_plugin(md: MarkdownIt, mode: Mode) -> None`
  - `def construire_markdown(mode: Mode) -> MarkdownIt`
  - `def rendre_corps(source: str, mode: Mode) -> str`

Syntaxe d'une réponse rédigée, par le plugin `container` de mdit-py-plugins :

```markdown
:::reponse 3
Git est distribué : chaque poste possède une copie complète de l'historique.
:::
```

- [ ] **Step 1 : Écrire les tests qui échouent**

```python
def test_ins_devient_une_reponse_en_mode_complet():
    html = rendre_corps("Le hash fait <ins>40</ins> chiffres.", Mode.COMPLET)
    assert '<span class="reponse">40</span>' in html

def test_ins_devient_un_trou_calibre_en_mode_trous():
    html = rendre_corps("Le hash fait <ins>40</ins> chiffres.", Mode.TROUS)
    assert '<span class="trou" style="--car:2"></span>' in html
    assert "40" not in html

def test_lignes_en_mode_trous_ne_laissent_pas_la_reponse():
    html = rendre_corps(":::reponse 3\nParce que c'est distribué.\n:::", Mode.TROUS)
    assert '<div class="lignes" style="--n:3"></div>' in html
    assert "distribué" not in html

def test_lignes_en_mode_complet_rendent_la_reponse():
    html = rendre_corps(":::reponse 3\nParce que c'est distribué.\n:::", Mode.COMPLET)
    assert '<div class="reponse-bloc">' in html and "distribué" in html
```

- [ ] **Step 2 : Vérifier l'échec** — Run : `uv run pytest tests/test_trous.py tests/test_lignes.py -v` → FAIL

- [ ] **Step 3 : Implémenter**

`--car` vaut le nombre de caractères de la réponse ; la largeur est calculée en CSS à la tâche 6. `construire_markdown` active `html=True`, les tables, puis les trois greffons.

- [ ] **Step 4 : Vérifier le succès** — Run : `uv run pytest tests/ -v` → PASS

- [ ] **Step 5 : Commit**

```bash
git add src tests && git commit -m "feat: trous et lignes de réponse selon le mode"
```

---

## Task 5 : Gabarit, cartouche et sortie PDF

**Files:**
- Create: `src/cielircours/rendu.py`, `gabarits/cours.html.j2`
- Test: `tests/test_rendu.py`

**Interfaces:**
- Consumes : `Cours` (tâche 2), `rendre_corps`, `Mode` (tâche 4)
- Produces :
  - `@dataclass(frozen=True) class Publication` — `version: str`, `date: datetime.date` ; propriété `libelle: str` qui vaut `"v1.02 du 29.10.26"`
  - `class SourceIntrouvable(FileNotFoundError)`
  - `def rendre_html(source: str, cours: Cours, pub: Publication, mode: Mode) -> str`
  - `def ecrire_pdf(html: str, base_url: Path, sortie: Path) -> None`

Le gabarit place le cartouche (discipline, classe, séquence, type, titre, établissement, durée, `pub.libelle`), les capacités attendues, la licence, le corps, et les pieds de page.

- [ ] **Step 1 : Écrire les tests qui échouent**

```python
def test_le_cartouche_porte_la_version():
    html = rendre_html("# T", cours, Publication("v1.02", date(2026, 10, 29)), Mode.TROUS)
    assert "v1.02 du 29.10.26" in html

def test_le_titre_est_echappe():            # Review Focus 3
    c = replace(cours, titre="Tableaux & vecteurs <avancés>")
    assert "Tableaux &amp; vecteurs &lt;avancés&gt;" in rendre_html("# T", c, pub, Mode.TROUS)

def test_un_cours_sans_trou_se_rend_quand_meme(tmp_path):   # Review Focus 1
    html = rendre_html("# T\n\nUn paragraphe sans trou.", cours, pub, Mode.TROUS)
    ecrire_pdf(html, tmp_path, tmp_path / "x.pdf")
    assert (tmp_path / "x.pdf").stat().st_size > 0

def test_image_absente_fait_echouer(tmp_path):              # Review Focus 5
    html = rendre_html("![s](img/absent.svg)", cours, pub, Mode.COMPLET)
    with pytest.raises(SourceIntrouvable):
        ecrire_pdf(html, tmp_path, tmp_path / "x.pdf")
```

- [ ] **Step 2 : Vérifier l'échec** — Run : `uv run pytest tests/test_rendu.py -v` → FAIL

- [ ] **Step 3 : Implémenter**

Jinja2 avec `autoescape=True`. `ecrire_pdf` branche un `url_fetcher` WeasyPrint qui lève `SourceIntrouvable` au lieu de laisser passer une ressource manquante.

- [ ] **Step 4 : Vérifier le succès** — Run : `uv run pytest tests/test_rendu.py -v` → PASS

- [ ] **Step 5 : Commit**

```bash
git add src gabarits tests && git commit -m "feat: gabarit, cartouche et sortie PDF"
```

---

## Task 6 : `cours.css` — la fiche compacte

**Files:**
- Create: `themes/cours.css`, `themes/polices/` (woff2 + `LICENCES.md`)
- Test: `tests/test_cours_css.py`

**Interfaces:**
- Consumes : les classes émises aux tâches 3 à 5 — `.alerte--{note,astuce,important,attention,danger}`, `.trou[style*="--car"]`, `.lignes`, `.reponse`, `.reponse-bloc`, `.bande`, `.terminal`, `.cartouche`.

Référence visuelle : `~/transfert/C01_introCpp_fiche_a_trous.pdf`. Vocabulaire à transposer : `workspace_LaTex/macros.sty`.

- [ ] **Step 1 : Écrire les tests qui échouent**

```python
def test_les_encadres_restent_distincts_en_niveaux_de_gris():
    fonds = luminances_des_fonds(Path("themes/cours.css"))   # {classe: L*}
    for a, b in combinations(fonds.values(), 2):
        assert abs(a - b) >= 8          # ΔL* minimal entre deux fonds d'encadré

def test_rien_ne_se_coupe_entre_deux_pages():
    css = Path("themes/cours.css").read_text()
    for sel in (".trou", ".lignes", ".bande", ".alerte", "table"):
        assert f"break-inside: avoid" in regle(css, sel)

def test_les_etiquettes_remplissables_disparaissent_en_mode_trous():
    css = Path("themes/cours.css").read_text()
    assert "body.trous .remplissable" in css and "visibility: hidden" in regle(css, "body.trous .remplissable")

def test_les_polices_sont_locales():
    css = Path("themes/cours.css").read_text()
    assert "https://" not in css
    assert list(Path("themes/polices").glob("*.woff2"))

def test_un_trou_long_ne_deborde_pas(tmp_path):              # Review Focus 2
    long = "une phrase entière de réponse qui ne tient pas sur une ligne"
    pages = pages_rendues(f"Réponse : <ins>{long}</ins>.", Mode.TROUS, tmp_path)
    assert debordement_horizontal(pages) == []
```

`luminances_des_fonds`, `regle`, `pages_rendues` et `debordement_horizontal` sont des utilitaires de `tests/outils.py`, à écrire dans cette étape : les deux derniers s'appuient sur `weasyprint.HTML(...).render()` et parcourent `document.pages`.

- [ ] **Step 2 : Vérifier l'échec** — Run : `uv run pytest tests/test_cours_css.py -v` → FAIL

- [ ] **Step 3 : Implémenter**

`@page` A4, marges 1,5 cm, en-tête et pied récurrents, numérotation `compteur / total`. Bandeaux de partie gris à filet noir à gauche. `.trou` : largeur `calc(var(--car) * 0.62em + 1.5em)`, bordure basse pointillée, `max-width: 100%`. Interligne plus large en mode trous via une classe sur `<body>`. Polices : une grotesque libre proche d'Helvetica et Inconsolata, déposées en woff2 avec leur licence.

- [ ] **Step 4 : Vérifier le succès** — Run : `uv run pytest tests/test_cours_css.py -v` → PASS

- [ ] **Step 5 : Commit**

```bash
git add themes tests && git commit -m "feat: feuille de style du document papier"
```

---

## Task 7 : Contrôle d'information personnelle

**Files:**
- Create: `src/cielircours/confidentialite.py`, `motifs.yml`
- Test: `tests/test_confidentialite.py`

**Interfaces:**
- Produces :
  - `@dataclass(frozen=True) class Infraction` — `fichier: Path`, `ligne: int`, `motif: str`, `extrait: str`
  - `def controler(racine: Path, motifs: Path) -> list[Infraction]`

`motifs.yml` liste des expressions nommées : `courriel`, `telephone`, `nom_enseignant`. Sont ignorés `.git/`, et tout chemin listé dans `.cielir-ignore` s'il existe.

- [ ] **Step 1 : Écrire les tests qui échouent**

```python
def test_detecte_une_adresse_de_courriel(tmp_path):
    (tmp_path / "slides.md").write_text("📧 [prof.fictif@lycee-fictif.fr](mailto:prof.fictif@lycee-fictif.fr)")
    infractions = controler(tmp_path, Path("motifs.yml"))
    assert [i.motif for i in infractions] == ["courriel", "courriel"]

def test_detecte_un_telephone_francais(tmp_path):
    (tmp_path / "a.md").write_text("Tel : 06 00 00 00 00")
    assert controler(tmp_path, Path("motifs.yml"))[0].motif == "telephone"

def test_un_etablissement_n_est_pas_une_infraction(tmp_path):
    (tmp_path / "a.md").write_text("Lycée Louis Rascol, Albi")
    assert controler(tmp_path, Path("motifs.yml")) == []
```

- [ ] **Step 2 : Vérifier l'échec** — Run : `uv run pytest tests/test_confidentialite.py -v` → FAIL

- [ ] **Step 3 : Implémenter**

Parcours des fichiers texte du dépôt, une expression compilée par motif, une infraction par occurrence avec le numéro de ligne et un extrait tronqué à 80 caractères. L'historique git n'est pas inspecté.

- [ ] **Step 4 : Vérifier le succès** — Run : `uv run pytest tests/test_confidentialite.py -v` → PASS

- [ ] **Step 5 : Commit**

```bash
git add src motifs.yml tests && git commit -m "feat: contrôle d'information personnelle"
```

---

## Task 8 : Injection de la version dans le deck

**Files:**
- Create: `src/cielircours/deck.py`
- Test: `tests/test_deck.py`

**Interfaces:**
- Consumes : `Publication` (tâche 5)
- Produces : `def preparer_deck(source: str, pub: Publication) -> str`

Marp ne permet pas de surcharger `footer` en ligne de commande : on réécrit une copie du deck, jamais la source.

- [ ] **Step 1 : Écrire les tests qui échouent**

```python
def test_le_pied_recoit_la_version():
    sortie = preparer_deck(DECK, Publication("v1.02", date(2026, 10, 29)))
    assert "footer: 'BTS CIEL-IR · Git et GitHub · 1re année · v1.02 du 29.10.26'" in sortie

def test_la_premiere_slide_recoit_la_version():
    premiere = preparer_deck(DECK, PUB).split("\n---\n")[1]
    assert "**v1.02** — 29 octobre 2026" in premiere

def test_la_source_n_est_pas_modifiee():
    avant = DECK
    preparer_deck(DECK, PUB)
    assert DECK == avant

def test_un_deck_sans_pied_en_recoit_un():
    assert "footer:" in preparer_deck(DECK_SANS_PIED, PUB)
```

- [ ] **Step 2 : Vérifier l'échec** — Run : `uv run pytest tests/test_deck.py -v` → FAIL

- [ ] **Step 3 : Implémenter**

Découpe de l'en-tête YAML entre les deux premiers `---`, ajout ou complément de `footer`, puis insertion d'une ligne en fin de première slide. Date en toutes lettres pour la slide, format court pour le pied.

- [ ] **Step 4 : Vérifier le succès** — Run : `uv run pytest tests/test_deck.py -v` → PASS

- [ ] **Step 5 : Commit**

```bash
git add src tests && git commit -m "feat: injection de la version dans une copie du deck"
```

---

## Task 9 : Ligne de commande, Makefile et dépôt témoin

**Files:**
- Create: `src/cielircours/cli.py`, `Makefile`, `temoin/` (`cours.yml`, `COURS.md`, `slides/01-temoin.md`, `slides/img/schema.svg`)
- Test: `tests/test_cli.py`, `tests/test_temoin.py`

**Interfaces:**
- Consumes : tout ce qui précède
- Produces :
  - `cielir-cours pdf COURS.md --config cours.yml --mode complet|trous --version v1.02 --date 2026-10-29 -o cours.pdf`
  - `cielir-cours deck slides/01.md --version v1.02 --date 2026-10-29 -o /tmp/deck.md`
  - `cielir-cours verifier .` — code de sortie 1 et liste des infractions

Le témoin couvre **tous** les éléments de mise en page : trous courts et longs, lignes de réponse, les cinq alertes, bloc terminal, tableau avec trous, code coloré, deux parties, et un **schéma SVG à compléter** — un seul fichier, dont les étiquettes portent la classe `remplissable` que `cours.css` masque en mode trous. C'est la réponse au § 6.7 : une seule source, pas deux fichiers à tenir d'équerre.

- [ ] **Step 1 : Écrire les tests qui échouent**

```python
def test_verifier_sort_en_erreur_si_infraction(tmp_path, capsys):
    (tmp_path / "a.md").write_text("contact@exemple.fr")
    assert main(["verifier", str(tmp_path)]) == 1

def test_le_temoin_tient_en_trois_pages_au_plus(tmp_path):
    for mode in ("complet", "trous"):
        main(["pdf", "temoin/COURS.md", "--config", "temoin/cours.yml", "--mode", mode,
              "--version", "v1.01", "--date", "2026-10-29", "-o", str(tmp_path / f"{mode}.pdf")])
        assert len(PdfReader(tmp_path / f"{mode}.pdf").pages) <= 3

def test_le_temoin_est_propre():
    assert main(["verifier", "temoin"]) == 0

def test_les_polices_sont_embarquees(tmp_path):
    ...  # PdfReader : /FontFile2 ou /FontFile3 présent pour chaque police
```

- [ ] **Step 2 : Vérifier l'échec** — Run : `uv run pytest tests/test_cli.py tests/test_temoin.py -v` → FAIL

- [ ] **Step 3 : Implémenter**

`argparse` à trois sous-commandes. Le `Makefile` expose `make temoin`, `make test`, et `make slides` qui appelle Marp par Docker avec `CHROME_NO_SANDBOX=1`.

- [ ] **Step 4 : Vérifier le succès**

Run : `uv run pytest -v && make temoin`
Attendu : tous les tests passent, et les trois PDF du témoin sont produits. **Les relire à l'œil** et les comparer à `~/transfert/C01_introCpp_fiche_a_trous.pdf`, en couleur puis convertis en niveaux de gris.

- [ ] **Step 5 : Commit**

```bash
git add src Makefile temoin tests && git commit -m "feat: ligne de commande et dépôt témoin"
```

---

## Task 10 : Action composite et workflow de publication

**Files:**
- Create: `action.yml` (remplace celui de la tâche 1), `gabarits/publier.yml`
- Test: `tests/test_tag.py`, plus une exécution réelle sur le témoin

**Interfaces:**
- Consumes : la ligne de commande (tâche 9)
- Produces : `uses: ciel-ir-rascol/cielir-cours-kit@v1` avec l'entrée `version` ; `gabarits/publier.yml`, copié tel quel dans chaque dépôt de cours.

- [ ] **Step 1 : Écrire le test qui échoue**

```python
@pytest.mark.parametrize("tag", ["v1.2", "1.01", "v1.01-rc", "v1.012"])
def test_un_tag_malforme_est_refuse(tag):       # Review Focus 4
    assert not TAG_VALIDE.match(tag)

def test_un_tag_conforme_est_accepte():
    assert TAG_VALIDE.match("v1.01") and TAG_VALIDE.match("v12.03")
```

`TAG_VALIDE` est exporté par `cielircours.cli` et repris par l'action.

- [ ] **Step 2 : Vérifier l'échec** — Run : `uv run pytest tests/test_tag.py -v` → FAIL

- [ ] **Step 3 : Implémenter**

`action.yml` : entrée `version`, étapes — refus immédiat si le tag ne vaut pas `TAG_VALIDE`, installation du paquet, `cielir-cours verifier .`, génération des deux PDF papier, préparation du deck puis Marp en conteneur, dépôt du tout dans `dist/`.

`gabarits/publier.yml` : déclenché sur `push: tags: ['v*']`, trois jobs — `construire` (appelle l'action, publie `dist/` en artefact), `pages` (déploie `dist/slides/`), `release` (`gh release create` avec les trois PDF et, dans les notes, le SHA du kit utilisé).

- [ ] **Step 4 : Valider sur le témoin, pour de vrai**

Pousser le témoin comme dépôt public `ciel-ir-rascol/cielir-cours-temoin`, activer Pages sur « GitHub Actions », taguer `v1.01`.
Run : `gh run watch --repo ciel-ir-rascol/cielir-cours-temoin`
Attendu : succès, trois PDF attachés à la release, Pages en ligne. Puis pousser un tag `v1.2` : la publication doit s'arrêter avec un message explicite.

- [ ] **Step 5 : Figer `v1` et commiter**

```bash
git tag -f v1 && git push -f origin v1
git add action.yml gabarits tests && git commit -m "feat: action composite et workflow de publication"
```

---

## Task 11 : `git-cours01-decouverte` → `git-c01-decouverte`

**Files:**
- Modify: le dépôt `cielir/git-cours01-decouverte`
- Create: `docs/specs/procedure-mise-en-conformite.md` (dans le kit)

**Interfaces:**
- Consumes : l'action en `v1` (tâche 10)
- Produces : la procédure écrite, dont la tâche 13 fera le mode « Mettre en conformité » du skill.

- [ ] **Step 1 : Renommer et réorganiser**

```bash
gh repo rename git-c01-decouverte --repo ciel-ir-rascol/git-cours01-decouverte
```

Puis, en local : `cours.yml`, `publier.yml`, suppression de `build.sh`, `.github/workflows/pages.yml`, `slides/themes/`, `slides/output/`, `workspace_LaTex/`. Le deck et `.vscode/` sont conservés, le thème étant désormais référencé par URL.

- [ ] **Step 2 : Convertir le `.tex` en `COURS.md`**

Les `\trou{x}` deviennent `<ins>x</ins>`, les `\lignes{n}{x}` des blocs `:::reponse n`, les `tcolorbox` des alertes, l'environnement `terminal` un bloc de code. Les schémas TikZ sont redessinés en SVG dans `slides/img/`. **Devant une macro qu'on ne sait pas transposer, s'arrêter et demander** — ne jamais laisser de syntaxe brute.

- [ ] **Step 3 : Vérifier avant de publier**

Run : `cielir-cours verifier . && make -f <kit>/Makefile temoin` sur ce dépôt
Attendu : aucune infraction ; les deux PDF produits, relus, et comparés au `Cours01_Git_Decouverte.pdf` d'origine pour s'assurer qu'aucun contenu n'a été perdu.

- [ ] **Step 4 : Publier**

```bash
git tag v1.01 && git push origin main --tags
gh run watch
```

Attendu : release avec trois PDF, Pages en ligne. Reprendre l'URL Pages dans la progression `tracker` et partout où l'ancienne a été diffusée.

- [ ] **Step 5 : Consigner et commiter la procédure**

Écrire dans le kit ce qui a réellement été fait, étape par étape, avec les pièges rencontrés.

```bash
git add docs/specs/procedure-mise-en-conformite.md
git commit -m "docs: procédure de mise en conformité, tirée de git-c01-decouverte"
```

---

## Task 12 : `cpp-c04-tableauxVecteurs`

**Files:**
- Create: le dépôt `cielir/cpp-c04-tableauxVecteurs`
- Create: `docs/specs/procedure-conversion.md` (dans le kit)

**Interfaces:**
- Consumes : l'action en `v1`, la procédure de la tâche 11
- Produces : la procédure de conversion, dont la tâche 13 fera le mode « Convertir ».

Source : `ciel-ir-rascol.github.io/docs/cpp/04-tableauxVecteurs/` — la page ne contient qu'un lien ; la matière est dans `slides-tableauxVecteurs.md` (338 lignes) et `assets/`.

- [ ] **Step 1 : Créer le dépôt et récupérer la matière**

Dossier local, dépôt public, `cours.yml`, `publier.yml`. Les SVG d'`assets/` sont repris tels quels dans `slides/img/`.

- [ ] **Step 2 : Écrire le `COURS.md` à partir du deck**

Il n'existe aucun cours rédigé : le prendre du deck, à la densité de la fiche, avec les trous posés sur ce qui doit passer par la main de l'étudiant. Faire valider le plan avant de rédiger.

- [ ] **Step 3 : Reprendre le deck au thème `ciel`**

Retirer le style en ligne, l'en-tête resté du C03, la ligne `Release : v1.0 (23.09.23)`, le lien vers `cpp-cours` qui n'existe plus, et **l'adresse de courriel de la page de titre**.

- [ ] **Step 4 : Vérifier puis publier**

Run : `cielir-cours verifier .`
Attendu : aucune infraction — ce dépôt est le test grandeur nature du contrôle.
Puis `git tag v1.01 && git push origin main --tags`, et relire les trois PDF.

- [ ] **Step 5 : Consigner et commiter la procédure**

```bash
git add docs/specs/procedure-conversion.md
git commit -m "docs: procédure de conversion d'un article du site"
```

---

## Task 13 : Le skill `cours-cielir`

**Files:**
- Create: `~/repos/claude-skills/` — `skills/cours-cielir/SKILL.md`, `install.sh`, `README.md`
- Move: `~/.claude/skills/infra-cielir/` vers ce dépôt

**Interfaces:**
- Consumes : les deux procédures écrites aux tâches 11 et 12, et la version du kit alors figée.

Le skill vient en dernier : il est la mise au propre de ce qu'on a réellement fait, pas une anticipation.

- [ ] **Step 1 : Créer le dépôt et le script d'installation**

`install.sh` pose un lien symbolique de chaque dossier de `skills/` vers `~/.claude/skills/`, sans écraser un dossier qui n'est pas un lien. `infra-cielir` y est déplacé puis relié.

- [ ] **Step 2 : Écrire `SKILL.md`**

En-tête `name` et `description` déclenchant sur « cours CIEL-IR », « nouveau cours », « mettre en conformité un dépôt de cours », « convertir un article du site ». Trois modes, chacun renvoyant à sa procédure. Les règles qui ne se déduisent pas du kit : convention de nommage, ce qu'un dépôt de cours contient et ne contient pas, le schéma de version, l'interdiction d'information personnelle, et la version du kit attendue.

- [ ] **Step 3 : Vérifier l'installation**

Run : `./install.sh && ls -la ~/.claude/skills/`
Attendu : `cours-cielir` et `infra-cielir` sont des liens vers le dépôt.

- [ ] **Step 4 : Éprouver le skill**

Lancer le mode « Créer » sur un bloc court dans une session neuve, et vérifier qu'il produit un dépôt conforme sans qu'on ait à le reprendre.

- [ ] **Step 5 : Commit**

```bash
git add . && git commit -m "feat: skill cours-cielir et dépôt des skills"
```
