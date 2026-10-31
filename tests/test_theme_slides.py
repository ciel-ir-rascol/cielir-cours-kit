"""Conventions du thème des slides : pagination avec total, logo en haut à droite, page de titre."""

import re
from pathlib import Path

from outils import regle

CSS = (Path(__file__).resolve().parents[1] / "themes" / "ciel.css").read_text(encoding="utf-8")


def test_la_pagination_porte_le_total():
    corps = regle(CSS, "section[data-marpit-pagination]::after")
    assert "attr(data-marpit-pagination)" in corps and "attr(data-marpit-pagination-total)" in corps


def test_le_logo_n_a_aucun_effet_sans_la_variable():
    pseudo = regle(CSS, "section:not(.lead):not(.chapitre)::before")
    assert "var(--logo, none)" in pseudo  # sans logo : pas d'image de fond
    assert "var(--logo-reserve, 0px)" in regle(CSS, "section:not(.lead):not(.chapitre) h2")


def test_le_logo_tient_au_dessus_du_filet_et_dans_les_marges():
    pseudo = regle(CSS, "section:not(.lead):not(.chapitre)::before")
    haut, hauteur = (int(re.search(rf"{p}:\s*(\d+)px", pseudo).group(1)) for p in ("top", "height"))
    assert re.search(r"right:\s*72px", pseudo)  # même marge droite que le contenu
    # le h2 : 1.35 em de 26 px, interligne 1.4 ; le filet est sous sa ligne
    ligne = 26 * 1.35 * 1.4
    assert haut == 64 and hauteur <= ligne  # ne descend pas jusqu'au filet
    largeur = int(re.search(r"width:\s*(\d+)px", pseudo).group(1))
    from cielircours.deck import RESERVE_LOGO

    assert int(RESERVE_LOGO.removesuffix("px")) > largeur  # le titre réserve plus que la largeur du logo


def test_la_page_de_titre_a_son_logo_et_son_pied():
    assert "section.lead .logo-titre" in CSS and "section.lead .pied-titre" in CSS


def test_les_classes_de_mise_en_page_vivent_dans_le_theme():
    for selecteur in (".cols", ".cols-3", ".photo", "figure", "figure img", "figcaption", ".credit", ".schema", ".petit"):
        assert regle(CSS, selecteur), selecteur
    assert "grid-template-columns: 1fr 1fr 1fr" in regle(CSS, ".cols-3")


def test_aucun_deck_ne_porte_de_bloc_style():
    racine = Path(__file__).resolve().parents[1]
    for deck in (racine / "temoin" / "slides").glob("[0-9][0-9]-*.md"):
        assert "<style" not in deck.read_text(encoding="utf-8"), deck
