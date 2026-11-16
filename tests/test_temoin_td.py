"""Le TD témoin : un TD jouet qui exerce tous les éléments d'un TD (voir temoin-td/)."""

from pathlib import Path

import pytest
from pypdf import PdfReader

from cielircours.cli import main
from cielircours.td import extraire_sujet

TEMOIN = Path(__file__).resolve().parent.parent / "temoin-td"


@pytest.fixture(scope="module")
def textes(tmp_path_factory) -> dict[str, str]:
    dossier = tmp_path_factory.mktemp("temoin-td")
    code = main(["td", str(TEMOIN), "--version", "v1.01", "--date", "2026-11-16",
                 "-o", str(dossier), "--exemplaire", "corrige"])
    assert code == 0
    return {nom: " ".join(p.extract_text() for p in PdfReader(dossier / f"{nom}.pdf").pages)
            for nom in ("sujet", "corrige")}


def test_sujet_sans_reponse(textes):
    assert "TEMOIN-REPONSE" not in textes["sujet"]
    assert "TEMOIN-ETIQUETTE" not in textes["sujet"]
    assert "1..*" not in textes["sujet"]


def test_corrige_avec_reponses(textes):
    assert textes["corrige"].count("TEMOIN-REPONSE") == 2
    assert "TEMOIN-ETIQUETTE" in textes["corrige"]


@pytest.mark.parametrize("nom", ["sujet", "corrige"])
def test_numerotation(textes, nom):
    texte = textes[nom].upper()
    for attendu in ("Q1.", "Q2.", "Q3.", "DT1 - CLASSE LECTEUR", "DR1 - ASSOCIATION", "RESSOURCE - MULTIPLICITÉS"):
        assert attendu in texte
    assert "AUTO-ÉVALUATION" in texte


def test_extraire_le_temoin(tmp_path):
    extraire_sujet(TEMOIN, tmp_path / "sujet")
    td = (tmp_path / "sujet" / "TD.md").read_text(encoding="utf-8")
    assert 'class="reponse"' not in td and "TEMOIN-REPONSE" not in td
