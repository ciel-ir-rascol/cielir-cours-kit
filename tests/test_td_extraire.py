"""`extraire_sujet` : le dépôt sujet d'un TD, sans aucune réponse."""

import shutil
from pathlib import Path

import pytest

from cielircours.schemas import filtrer_svg
from cielircours.supports import retirer_blocs
from cielircours.td import extraire_sujet

DONNEES = Path(__file__).parent / "data"
SOURCE = ("## A\n\n**Q.** Combien ?\n\n"
          '<div class="reponse">\n\nSECRET\n\n</div>\n\n**Q.** Compléter le DR1.\n')
SVG_A = ('<svg xmlns="http://www.w3.org/2000/svg"><rect width="5" height="5"/>'
         '<text class="remplissable">ETIQUETTE</text></svg>')
SVG_B = '<svg xmlns="http://www.w3.org/2000/svg"><rect width="5" height="5"/></svg>'
PNG = b"\x89PNG\r\n\x1a\n" + bytes(range(40))


@pytest.fixture
def depots(tmp_path) -> tuple[Path, Path]:
    corr, sujet = tmp_path / "x-td01-y-CORR", tmp_path / "x-td01-y"
    (corr / "img").mkdir(parents=True)
    sujet.mkdir()
    shutil.copy(DONNEES / "td.yml", corr / "td.yml")
    (corr / "TD.md").write_text(SOURCE, encoding="utf-8")
    (corr / "img" / "a.svg").write_text(SVG_A, encoding="utf-8")
    (corr / "img" / "b.svg").write_text(SVG_B, encoding="utf-8")
    (corr / "img" / "c.png").write_bytes(PNG)
    return corr, sujet


def test_ecrit_td_md_sans_reponse(depots):
    corr, sujet = depots
    extraire_sujet(corr, sujet)
    td = (sujet / "TD.md").read_text(encoding="utf-8")
    assert td == retirer_blocs(SOURCE, "reponse")
    assert "SECRET" not in td and "**Q.** Combien ?" in td


def test_copie_td_yml_a_l_identique(depots):
    corr, sujet = depots
    extraire_sujet(corr, sujet)
    assert (sujet / "td.yml").read_bytes() == (corr / "td.yml").read_bytes()


def test_svg_vide_de_ses_remplissables(depots):
    corr, sujet = depots
    extraire_sujet(corr, sujet)
    octets = (sujet / "img" / "a.svg").read_bytes()
    assert octets == filtrer_svg((corr / "img" / "a.svg").read_bytes())
    assert b"ETIQUETTE" not in octets


def test_svg_sans_remplissable_identique(depots):
    corr, sujet = depots
    extraire_sujet(corr, sujet)
    assert (sujet / "img" / "b.svg").read_bytes() == (corr / "img" / "b.svg").read_bytes()


def test_autres_images_copiees(depots):
    corr, sujet = depots
    ecrits = extraire_sujet(corr, sujet)
    assert (sujet / "img" / "c.png").read_bytes() == PNG
    assert sorted(map(str, ecrits)) == ["TD.md", "img/a.svg", "img/b.svg", "img/c.png", "td.yml"]


def test_ne_touche_que_ses_fichiers(depots):
    corr, sujet = depots
    (sujet / "README.md").write_text("à moi", encoding="utf-8")
    extraire_sujet(corr, sujet)
    assert (sujet / "README.md").read_text(encoding="utf-8") == "à moi"


def test_relecture_refuse_une_fuite(depots):
    corr, sujet = depots
    # pas du XML : filtrer_svg le rend tel quel, et le mot passerait dans le sujet
    (corr / "img" / "d.svg").write_text("pas du xml remplissable", encoding="utf-8")
    with pytest.raises(ValueError, match="img/d.svg"):
        extraire_sujet(corr, sujet)
    assert not (sujet / "TD.md").exists()
    assert not (sujet / "img").exists()


def test_reponse_dans_un_bloc_de_code_refusee(depots):
    corr, sujet = depots
    (corr / "TD.md").write_text(SOURCE + '\n```html\n<div class="reponse">\n```\n', encoding="utf-8")
    with pytest.raises(ValueError, match="TD.md"):
        extraire_sujet(corr, sujet)
