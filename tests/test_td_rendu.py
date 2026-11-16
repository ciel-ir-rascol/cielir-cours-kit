"""Rendu HTML et PDF d'un TD : cartouche, auto-évaluation, sujet sans réponse."""

import dataclasses
from datetime import date
from pathlib import Path

import pytest
from pypdf import PdfReader

from cielircours.config import lire_td
from cielircours.rendu import Publication, ecrire_pdf_td, rendre_html_td
from cielircours.td import Exemplaire

TD = lire_td(Path(__file__).parent / "data" / "td.yml")
PUB = Publication("v1.02", date(2026, 11, 16))

SVG = ('<svg xmlns="http://www.w3.org/2000/svg" width="200" height="60">'
       '<rect x="1" y="1" width="198" height="58" fill="none" stroke="black"/>'
       '<text x="10" y="35" class="remplissable">ETIQUETTE-SECRETE</text></svg>')

SOURCE = (
    "## Partie\n\n"
    "**Q.** Combien de compartiments a une classe ?\n\n"
    '<div class="reponse">\n\nREPONSE-SECRETE : trois.\n\n</div>\n\n'
    "**Q.** Compléter le DR1.\n\n"
    '<div class="dr" titre="Relations">\n\n![schéma](img/dr.svg)\n\n</div>\n'
)


@pytest.fixture(scope="module")
def pdfs(tmp_path_factory) -> dict[Exemplaire, Path]:
    racine = tmp_path_factory.mktemp("td")
    (racine / "img").mkdir()
    (racine / "img" / "dr.svg").write_text(SVG, encoding="utf-8")
    sorties = {}
    for ex in Exemplaire:
        sortie = racine / f"{ex.value}.pdf"
        ecrire_pdf_td(rendre_html_td(SOURCE, TD, PUB, ex), racine, sortie, ex)
        sorties[ex] = sortie
    return sorties


def _pages(chemin: Path) -> list[str]:
    return [p.extract_text() for p in PdfReader(chemin).pages]


@pytest.mark.parametrize("ex,libelle", [(Exemplaire.SUJET, "Sujet"), (Exemplaire.CORRIGE, "Corrigé")])
def test_cartouche(ex, libelle):
    html = rendre_html_td(SOURCE, TD, PUB, ex)
    assert f'<span class="type">{libelle}</span>' in html
    assert "TD01 - Diagramme de classes UML" in html
    assert PUB.libelle in html


def test_autoevaluation():
    assert "autoevaluation" not in rendre_html_td(SOURCE, TD, PUB, Exemplaire.SUJET)  # par défaut
    avec = dataclasses.replace(TD, autoevaluation=True)
    html = rendre_html_td(SOURCE, avec, PUB, Exemplaire.SUJET)
    assert '<section class="autoevaluation">' in html
    for c in TD.capacites + ["Acquis", "En cours", "Non acquis"]:
        assert c in html
    sans = dataclasses.replace(TD, autoevaluation=False)
    assert "autoevaluation" not in rendre_html_td(SOURCE, sans, PUB, Exemplaire.SUJET)


def test_sujet_pdf_sans_reponse(pdfs):
    sujet = " ".join(_pages(pdfs[Exemplaire.SUJET]))
    corrige = " ".join(_pages(pdfs[Exemplaire.CORRIGE]))
    assert "Q1." in sujet and "DR1 - RELATIONS" in sujet.upper()
    assert "REPONSE-SECRETE" not in sujet and "ETIQUETTE-SECRETE" not in sujet
    assert "REPONSE-SECRETE" in corrige and "ETIQUETTE-SECRETE" in corrige


def test_dr_sur_sa_page(pdfs):
    pages = _pages(pdfs[Exemplaire.CORRIGE])
    page_q = next(i for i, t in enumerate(pages) if "Q2." in t)
    page_dr = next(i for i, t in enumerate(pages) if "DR1 - RELATIONS" in t.upper())
    assert page_dr > page_q
