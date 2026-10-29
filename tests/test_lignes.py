import pytest

from cielircours.mdtext import Mode, rendre_corps


def test_lignes_en_mode_trous_ne_laissent_pas_la_reponse():
    html = rendre_corps(":::reponse 3\nParce que c'est distribué.\n:::", Mode.TROUS)
    assert '<div class="lignes" style="--n:3"></div>' in html
    assert "distribué" not in html


def test_lignes_en_mode_complet_rendent_la_reponse():
    html = rendre_corps(":::reponse 3\nParce que c'est distribué.\n:::", Mode.COMPLET)
    assert '<div class="reponse-bloc">' in html and "distribué" in html


def test_bloc_sans_nombre_de_lignes_est_refuse():
    with pytest.raises(ValueError, match="nombre de lignes"):
        rendre_corps(":::reponse\nsecret\n:::", Mode.TROUS)
