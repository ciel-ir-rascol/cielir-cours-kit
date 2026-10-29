import re
from dataclasses import replace
from datetime import date

import pytest

from cielircours.mdtext import Mode
from cielircours.rendu import Publication, SchemeInterdit, SourceIntrouvable, ecrire_pdf, rendre_html


def test_le_libelle_suit_le_format_du_cartouche_latex():
    assert Publication("v1.02", date(2026, 10, 29)).libelle == "v1.02 du 29.10.26"
    assert Publication("v1.10", date(2027, 1, 5)).libelle == "v1.10 du 05.01.27"


def test_le_cartouche_porte_la_version(cours):
    html = rendre_html("# T", cours, Publication("v1.02", date(2026, 10, 29)), Mode.TROUS)
    assert "v1.02 du 29.10.26" in html


def test_le_cartouche_porte_les_metadonnees(cours, pub):
    html = rendre_html("# T", cours, pub, Mode.COMPLET)
    for attendu in (
        "Informatique",
        "BTS CIEL-IR 1ère année",
        "cpp",
        "Tableaux et vecteurs",
        "Lycée Louis Rascol, Albi",
        "2 h",
        "Capacités attendues",
        "Manipuler un tableau",
        "Utiliser un vecteur",
        "CC BY-NC-SA 4.0",
    ):
        assert attendu in html


def test_le_titre_est_echappe(cours, pub):  # Review Focus 3
    c = replace(cours, titre="Tableaux & vecteurs <avancés>")
    assert "Tableaux &amp; vecteurs &lt;avancés&gt;" in rendre_html("# T", c, pub, Mode.TROUS)


def test_sans_capacites_pas_de_section_vide(cours, pub):
    html = rendre_html("# T", replace(cours, capacites=[]), pub, Mode.COMPLET)
    assert "Capacités attendues" not in html
    assert 'class="capacites"' not in html


def test_sans_duree_pas_de_duree_vide(cours, pub):
    html = rendre_html("# T", replace(cours, duree=""), pub, Mode.COMPLET)
    assert 'class="duree"' not in html


def test_le_mode_distingue_le_document(cours, pub):
    assert '<body class="mode-trous">' in rendre_html("# T", cours, pub, Mode.TROUS)
    assert '<body class="mode-complet">' in rendre_html("# T", cours, pub, Mode.COMPLET)


def test_le_corps_passe_par_le_rendu_markdown(cours, pub):
    assert 'class="trou"' in rendre_html("a <ins>bb</ins>", cours, pub, Mode.TROUS)
    assert 'class="reponse"' in rendre_html("a <ins>bb</ins>", cours, pub, Mode.COMPLET)


def test_aucune_information_personnelle(cours, pub):
    html = rendre_html("# T", cours, pub, Mode.COMPLET)
    assert not re.search(r"\S+@\S+\.\S+|\b0\d(?:[ .]?\d{2}){4}\b", html)


def test_un_cours_sans_trou_se_rend_quand_meme(cours, pub, tmp_path):  # Review Focus 1
    html = rendre_html("# T\n\nUn paragraphe sans trou.", cours, pub, Mode.TROUS)
    ecrire_pdf(html, tmp_path, tmp_path / "x.pdf")
    assert (tmp_path / "x.pdf").stat().st_size > 0


def test_le_pdf_contient_cartouche_et_corps(cours, pub, tmp_path):
    from pypdf import PdfReader

    html = rendre_html("# Mon corps\n\nBonjour.", cours, pub, Mode.COMPLET)
    ecrire_pdf(html, tmp_path, tmp_path / "x.pdf")
    texte = PdfReader(tmp_path / "x.pdf").pages[0].extract_text()
    assert "v1.02 du 29.10.26" in texte
    assert "Bonjour." in texte


def test_image_presente_se_rend(cours, pub, tmp_path):
    (tmp_path / "img").mkdir()
    (tmp_path / "img" / "ok.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"/>'
    )
    html = rendre_html("![s](img/ok.svg)", cours, pub, Mode.COMPLET)
    ecrire_pdf(html, tmp_path, tmp_path / "x.pdf")
    assert (tmp_path / "x.pdf").stat().st_size > 0


def test_image_absente_fait_echouer(cours, pub, tmp_path):  # Review Focus 5
    html = rendre_html("![s](img/absent.svg)", cours, pub, Mode.COMPLET)
    with pytest.raises(SourceIntrouvable, match="absent.svg"):
        ecrire_pdf(html, tmp_path, tmp_path / "x.pdf")
    assert not (tmp_path / "x.pdf").exists()


@pytest.mark.parametrize("url", ["http://exemple.invalid/s.svg", "https://exemple.invalid/s.svg"])
def test_image_distante_est_refusee(cours, pub, tmp_path, url):
    html = rendre_html(f"![s]({url})", cours, pub, Mode.COMPLET)
    with pytest.raises(SchemeInterdit, match="exemple.invalid"):
        ecrire_pdf(html, tmp_path, tmp_path / "x.pdf")
    assert not (tmp_path / "x.pdf").exists()
