"""Le dépôt témoin : un cours jouet qui exerce tous les éléments de mise en page.

Il est régénéré à chaque modification du kit ; le tag `v1` ne bouge que s'il se régénère
sans régression. Ces tests sont sa non-régression automatique, la relecture à l'œil du PDF
(en couleur et en niveaux de gris) étant le complément qu'ils ne remplacent pas.
"""

import re
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path

import pytest
from pypdf import PdfReader

from cielircours.cli import main
from cielircours.config import lire_config
from cielircours.mdtext import Mode
from cielircours.rendu import Publication, _FetcherStrict, rendre_html

RACINE = Path(__file__).resolve().parent.parent
TEMOIN = RACINE / "temoin"
VERSION, DATE = "v1.01", "2026-10-29"


@pytest.fixture(scope="module")
def pdfs(tmp_path_factory):
    dossier = tmp_path_factory.mktemp("temoin")
    for mode in ("complet", "trous"):
        code = main(["pdf", str(TEMOIN / "COURS.md"), "--config", str(TEMOIN / "cours.yml"),
                     "--mode", mode, "--version", VERSION, "--date", DATE, "-o", str(dossier / f"{mode}.pdf")])
        assert code == 0
    return dossier


def _texte(chemin: Path) -> str:
    return "\n".join(p.extract_text() for p in PdfReader(chemin).pages)


def _norme(texte: str) -> str:
    return " ".join(texte.split())


def _html(mode: Mode) -> str:
    cours = lire_config(TEMOIN / "cours.yml")
    source = (TEMOIN / "COURS.md").read_text(encoding="utf-8")
    return rendre_html(source, cours, Publication(VERSION, date.fromisoformat(DATE)), mode)


# ---------- les contraintes globales ----------

@pytest.mark.parametrize("mode", ["complet", "trous"])
def test_le_temoin_tient_en_trois_pages_au_plus(pdfs, mode):
    assert len(PdfReader(pdfs / f"{mode}.pdf").pages) <= 3


@pytest.mark.parametrize("mode", ["complet", "trous"])
def test_les_polices_sont_embarquees(pdfs, mode):
    polices = {}
    for page in PdfReader(pdfs / f"{mode}.pdf").pages:
        for f in page["/Resources"].get("/Font", {}).values():
            f = f.get_object()
            desc = f["/DescendantFonts"][0].get_object()["/FontDescriptor"] if "/DescendantFonts" in f else f["/FontDescriptor"]
            polices[str(f["/BaseFont"])] = {"/FontFile2", "/FontFile3", "/FontFile"} & set(desc.get_object())
    assert any("Liberation" in n for n in polices) and any("Inconsolata" in n for n in polices), polices
    assert all(polices.values()), polices


def test_le_temoin_est_propre():
    assert main(["verifier", str(TEMOIN)]) == 0


def test_la_version_n_est_ecrite_dans_aucune_source():
    for fichier in TEMOIN.rglob("*"):
        if fichier.is_file():
            texte = fichier.read_text(encoding="utf-8")
            assert not re.search(r"\bv\d+\.\d{2}\b|\d{2}\.\d{2}\.\d{2}\b", texte), fichier


def test_le_pdf_porte_la_version_injectee(pdfs):
    for mode in ("complet", "trous"):
        assert "v1.01 du 29.10.26" in _texte(pdfs / f"{mode}.pdf")


def test_aucun_fichier_genere_dans_le_temoin():
    assert not list(TEMOIN.rglob("*.pdf")) and not list(TEMOIN.rglob("*.html"))
    assert not (TEMOIN / "slides" / "output").exists()


# ---------- tous les éléments de mise en page ----------

@pytest.mark.parametrize("mode", [Mode.COMPLET, Mode.TROUS])
def test_le_temoin_exerce_les_elements_communs(mode):
    html = _html(mode)
    assert len(re.findall(r"<h2>", html)) >= 2  # au moins deux parties
    for alerte in ("note", "astuce", "important", "attention", "danger"):
        assert f"alerte--{alerte}" in html, alerte
    assert '<pre class="terminal">' in html
    assert '<pre class="code">' in html and '<span class="k">' in html  # code coloré
    tableau = re.search(r"<table>.*?</table>", html, re.DOTALL).group(0)
    assert re.search(r"<td>[^<]*<span class=\"(?:trou|reponse)\"", tableau)  # tableau contenant des trous
    assert 'alt="Chaîne de construction' in html and "slides/img/schema.svg" in html


def test_le_temoin_a_des_trous_courts_et_longs():
    longueurs = sorted(int(n) for n in re.findall(r'class="trou" style="--car:(\d+)"', _html(Mode.TROUS)))
    assert longueurs[0] <= 5 and longueurs[-1] >= 30, longueurs


def test_le_temoin_a_des_lignes_de_reponse():
    html = _html(Mode.TROUS)
    assert len(re.findall(r'<div class="lignes" style="--n:\d+">', html)) >= 2
    assert '<div class="reponse-bloc">' in _html(Mode.COMPLET)


# ---------- le schéma : un seul fichier ----------

def _etiquettes(arbre: ET.Element) -> list[str]:
    return [
        "".join(e.itertext()).strip()
        for e in arbre.iter()
        if "remplissable" in (e.get("class") or "").split()
    ]


def test_un_seul_fichier_svg_sert_au_cours_et_aux_slides():
    assert [p.relative_to(TEMOIN) for p in TEMOIN.rglob("*.svg")] == [Path("slides/img/schema.svg")]
    assert "slides/img/schema.svg" in (TEMOIN / "COURS.md").read_text(encoding="utf-8")
    assert "img/schema.svg" in (TEMOIN / "slides" / "01-temoin.md").read_text(encoding="utf-8")


def test_le_schema_a_des_etiquettes_a_completer_et_une_structure():
    arbre = ET.parse(TEMOIN / "slides" / "img" / "schema.svg").getroot()
    assert len(_etiquettes(arbre)) >= 5
    texte = " ".join(arbre.itertext())
    assert "Éditeur" in texte and "Étape 1" in texte


def test_le_recuperateur_vide_les_cases_du_schema():
    url = (TEMOIN / "slides" / "img" / "schema.svg").as_uri()
    complet = ET.fromstring(_FetcherStrict(Mode.COMPLET).fetch(url).read())
    trous = ET.fromstring(_FetcherStrict(Mode.TROUS).fetch(url).read())
    assert _etiquettes(complet) and _etiquettes(trous) == []
    assert "Éditeur" in " ".join(trous.itertext())  # la structure reste


# ---------- aucune réponse ne fuite dans le PDF à trous ----------

def _reponses() -> list[str]:
    source = (TEMOIN / "COURS.md").read_text(encoding="utf-8")
    ins = re.findall(r"<ins>(.*?)</ins>", source)
    blocs = re.findall(r"^:::reponse \d+\n(.*?)^:::", source, re.DOTALL | re.MULTILINE)
    svg = _etiquettes(ET.parse(TEMOIN / "slides" / "img" / "schema.svg").getroot())
    return [re.sub(r"[`*]", "", r) for r in ins + blocs + svg]


def test_chaque_reponse_disparait_du_pdf_a_trous(pdfs):
    complet, trous = _norme(_texte(pdfs / "complet.pdf")), _norme(_texte(pdfs / "trous.pdf"))
    reponses = _reponses()
    assert len(reponses) >= 20
    for r in reponses:
        r = _norme(r)
        assert complet.count(r) > trous.count(r), f"« {r} » reste en mode trous ({trous.count(r)} fois)"


def test_les_reponses_longues_sont_absentes_du_pdf_a_trous(pdfs):
    trous = _norme(_texte(pdfs / "trous.pdf"))
    longues = [_norme(r) for r in _reponses() if len(r) >= 20]
    assert len(longues) >= 3
    for r in longues:
        assert r not in trous, r


# ---------- le deck ----------

def test_le_deck_du_temoin_recoit_la_version(tmp_path):
    sortie = tmp_path / "deck.md"
    assert main(["deck", str(TEMOIN / "slides" / "01-temoin.md"), "--version", VERSION,
                 "--date", DATE, "-o", str(sortie)]) == 0
    texte = sortie.read_text(encoding="utf-8")
    assert "v1.01 du 29.10.26" in texte and "**v1.01** — 29 octobre 2026" in texte
    assert "BTS CIEL-IR" in texte  # le pied d'origine est conservé


# ---------- le Makefile ----------

def test_le_makefile_epingle_marp_et_desactive_le_bac_a_sable():
    makefile = (RACINE / "Makefile").read_text(encoding="utf-8")
    assert "marpteam/marp-cli:v4.5.1" in makefile
    assert "CHROME_NO_SANDBOX=1" in makefile
    assert ":latest" not in makefile
    for cible in ("temoin:", "test:", "slides:"):
        assert re.search(rf"^{cible}", makefile, re.MULTILINE), cible
