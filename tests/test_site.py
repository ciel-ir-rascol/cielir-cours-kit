"""`cielir-cours site` : l'accueil et la fiche en ligne ; et site.css, la feuille d'écran."""

import re
import shutil
from importlib.resources import files
from pathlib import Path

import pytest

from cielircours.cli import main
from outils import DONNEES, regle

SITE_CSS = Path(str(files("cielircours.donnees") / "themes" / "site.css"))
SOURCE = (
    "# C04 - Tableaux et vecteurs\n\n"
    "## Partie\n\nUn <ins>SECRET</ins> ici.\n\n"
    "```cpp\nint t[<ins>5</ins>];\n```\n\n"
    "| a | b |\n| - | - |\n| <ins>CELLULE</ins> | x |\n\n"
    '<ins lignes="2">REDIGEE</ins>\n\n'
    "![schéma](slides/img/x.svg)\n"
)
URL = "https://github.com/ciel-ir-rascol/cpp-c04-tableauxVecteurs"


@pytest.fixture
def depot(tmp_path, monkeypatch):
    monkeypatch.setenv("GITHUB_REPOSITORY", "ciel-ir-rascol/cpp-c04-tableauxVecteurs")
    d = tmp_path / "cours"
    (d / "slides" / "img").mkdir(parents=True)
    (d / "slides" / "img" / "x.svg").write_text("<svg xmlns='http://www.w3.org/2000/svg'/>")
    shutil.copy(DONNEES / "cours-cpp.yml", d / "cours.yml")
    (d / "COURS.md").write_text(SOURCE, encoding="utf-8")
    return d


@pytest.fixture
def site(depot, tmp_path):
    sortie = tmp_path / "dist" / "site"
    code = main(["site", str(depot / "COURS.md"), "--config", str(depot / "cours.yml"),
                 "--version", "v1.02", "--date", "2026-11-03", "-o", str(sortie)])
    assert code == 0
    return sortie


def test_le_site_ecrit_l_accueil_la_fiche_et_les_images(site):
    assert (site / "index.html").is_file()
    assert (site / "fiche" / "index.html").is_file()
    assert (site / "fiche" / "slides" / "img" / "x.svg").is_file()
    assert (site / "assets" / "site.css").is_file()
    assert not (site / "slides").exists()  # les slides sont l'affaire de Marp


def test_le_site_sert_ses_polices_lui_meme(site):
    css = (site / "assets" / "site.css").read_text(encoding="utf-8")
    for police in re.findall(r'url\("([^"]+)"\)', css):
        assert (site / "assets" / police).is_file(), police


def test_un_cours_sans_images_ne_fait_pas_echouer_le_site(depot, tmp_path):
    shutil.rmtree(depot / "slides")
    sortie = tmp_path / "s"
    assert main(["site", str(depot / "COURS.md"), "--version", "v1.02", "--date", "2026-11-03",
                 "-o", str(sortie)]) == 0
    assert not (sortie / "fiche" / "slides").exists()


def test_la_fiche_montre_les_reponses_sans_ins_residuel(site):
    html = (site / "fiche" / "index.html").read_text(encoding="utf-8")
    for reponse in ("SECRET", "CELLULE", "REDIGEE"):
        assert reponse in html
    assert 'class="reponse"' in html and "reponse-bloc" in html
    assert "<ins" not in html.lower()
    assert 'class="trou"' not in html and 'class="lignes"' not in html


def test_la_fiche_ne_repete_pas_le_titre_et_porte_l_entete_et_le_pied(site):
    html = (site / "fiche" / "index.html").read_text(encoding="utf-8")
    assert html.count("C04 - Tableaux et vecteurs</h1>") == 1
    assert "Informatique — 1CIELIR" in html
    assert "Release : v1.02 (03.11.26)" in html
    assert "J.Serrand" in html and f'href="{URL}"' in html
    assert 'href="../"' in html and 'href="../slides/"' in html
    assert 'href="../assets/site.css"' in html


def test_l_accueil_porte_les_trois_liens_dans_l_ordre(site):
    html = (site / "index.html").read_text(encoding="utf-8")
    liens = re.findall(r'<a href="([^"]+)"><strong>([^<]+)</strong>', html)
    assert liens == [
        ("fiche/", "La fiche de cours"),
        ("slides/", "Le diaporama"),
        (f"{URL}/releases/latest", "Les PDF à imprimer"),
    ]


def test_l_accueil_dit_le_cours_le_tp_et_la_release(site):
    html = (site / "index.html").read_text(encoding="utf-8")
    assert "C04 - Tableaux et vecteurs</h1>" in html
    assert "<code>tp04-tableaux</code>" in html
    assert "Release : v1.02 (03.11.26)" in html and "J.Serrand" in html
    assert "<img" not in html  # pas de logo : le chemin courant


def test_l_accueil_porte_le_logo_s_il_est_renseigne(depot, tmp_path):
    (depot / "slides" / "img" / "logo.svg").write_text("<svg xmlns='http://www.w3.org/2000/svg'/>")
    cfg = depot / "cours.yml"
    cfg.write_text(cfg.read_text(encoding="utf-8") + "logo: logo.svg\n", encoding="utf-8")
    sortie = tmp_path / "s"
    assert main(["site", str(depot / "COURS.md"), "--version", "v1.02", "--date", "2026-11-03",
                 "-o", str(sortie)]) == 0
    html = (sortie / "index.html").read_text(encoding="utf-8")
    assert 'src="assets/logo/logo.svg"' in html
    assert (sortie / "assets" / "logo" / "logo.svg").is_file()


def test_un_titre_divergent_n_ecrit_aucun_site(depot, tmp_path, capsys):
    (depot / "COURS.md").write_text("# Autre\n\n" + SOURCE, encoding="utf-8")
    sortie = tmp_path / "s"
    assert main(["site", str(depot / "COURS.md"), "--version", "v1.02", "--date", "2026-11-03",
                 "-o", str(sortie)]) == 2
    assert "attendu" in capsys.readouterr().err
    assert not sortie.exists()


def test_un_trou_mal_forme_arrete_le_site(depot, tmp_path):
    (depot / "COURS.md").write_text("Un <ins>a <ins>b</ins></ins>.\n", encoding="utf-8")
    assert main(["site", str(depot / "COURS.md"), "--version", "v1.02", "--date", "2026-11-03",
                 "-o", str(tmp_path / "s")]) == 2


def test_la_version_est_controlee(depot, tmp_path):
    with pytest.raises(SystemExit):
        main(["site", str(depot / "COURS.md"), "--version", "1.2", "--date", "2026-11-03", "-o", str(tmp_path)])


# ---------- site.css ----------

CSS = SITE_CSS.read_text(encoding="utf-8")


def test_pas_de_page_paginee_ni_de_ressource_distante():
    assert "@page" not in CSS
    assert "http://" not in CSS and "https://" not in CSS and "@import" not in CSS


def test_une_seule_largeur_pour_toute_la_page_et_viewport_mobile():
    # le texte est aussi large que le plus large des tableaux : rien ne paraît étriqué à côté
    # d'un bloc. 62rem tient le tableau le plus large des cours actuels, mesuré à 1039 px.
    assert re.search(r"max-width:\s*min\(62rem", regle(CSS, ".page"))
    assert "@media (max-width" in CSS


def test_le_h2_garde_son_filet_orange():
    assert "var(--c-accent)" in regle(CSS, "h2") and "#d9661f" in CSS.lower()


def test_les_reponses_sont_teintees_sans_rouge_ni_souligne_ni_gras():
    for sel in (".reponse", ".reponse-bloc"):
        corps = regle(CSS, sel)
        assert "background" in corps
        assert not re.search(r"font-weight|text-decoration|border-bottom|var\(--corr", corps), sel
    assert "--corr" not in CSS
    for teinte in re.findall(r"--c-reponse-[a-z-]+:\s*(#[0-9a-f]{6})", CSS):
        r, g, b = (int(teinte[i:i + 2], 16) for i in (1, 3, 5))
        assert g >= r and g >= b, teinte  # jamais rougeâtre


def test_les_etiquettes_remplissables_restent_visibles():
    assert "visibility: visible" in regle(CSS, ".remplissable")


def test_les_trous_et_les_lignes_ne_cassent_pas_la_page():
    assert "max-width: 100%" in regle(CSS, ".trou")
    assert "height" in regle(CSS, ".lignes")


def test_code_et_tableaux_defilent_au_lieu_de_deborder():
    assert "overflow-x: auto" in regle(CSS, "pre")
    assert "overflow-x: auto" in regle(CSS, "table")


def test_les_cinq_encadres_sont_stylés():
    for t in ("note", "astuce", "important", "attention", "danger"):
        assert "background" in regle(CSS, f".alerte--{t}"), t


def test_le_code_ne_passe_jamais_a_la_ligne_et_defile_dans_son_cadre():
    # passer à la ligne détruirait l'alignement en colonnes des commentaires ; un bloc plus
    # large que la page défile, il ne se replie pas et il n'est pas tronqué.
    corps = regle(CSS, "pre")
    assert "white-space: pre;" in corps and "overflow-x: auto" in corps
    assert "overflow-x: auto" in regle(CSS, ".corps > table") + regle(CSS, "table")
    # plus de débordement hors de la page : tout partage sa largeur
    assert "translateX(-50%)" not in CSS
