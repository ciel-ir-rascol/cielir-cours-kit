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


@pytest.mark.parametrize("source", [":::reponsefoo 3\nsecret\n:::", ":::reponse3\nsecret\n:::"])
def test_nom_de_bloc_voisin_de_reponse_est_refuse(source):
    with pytest.raises(ValueError, match="reponse"):
        rendre_corps(source, Mode.TROUS)


@pytest.mark.parametrize("params", ["0", "x", "-1", "2 3"])
def test_nombre_de_lignes_invalide_est_refuse(params):
    with pytest.raises(ValueError, match="nombre de lignes"):
        rendre_corps(f":::reponse {params}\nsecret\n:::", Mode.TROUS)


def test_autre_conteneur_n_est_pas_un_bloc_de_reponse():
    html = rendre_corps(":::note\ntexte\n:::", Mode.COMPLET)
    assert "reponse" not in html


def test_bloc_de_reponse_dans_une_liste_ne_fuite_pas():
    html = rendre_corps("- item\n\n  :::reponse 2\n  secret\n  :::", Mode.TROUS)
    assert "secret" not in html and 'class="lignes" style="--n:2"' in html


def test_deux_blocs_et_contenu_riche_en_mode_trous():
    src = ":::reponse 1\n**secret** `code`\n\n- liste\n:::\n\ntexte\n\n:::reponse 4\nautre\n:::"
    html = rendre_corps(src, Mode.TROUS)
    assert "secret" not in html and "autre" not in html and "liste" not in html
    assert "--n:1" in html and "--n:4" in html and "texte" in html


def test_greffons_refusent_un_mode_inattendu():
    from markdown_it import MarkdownIt

    from cielircours.plugins.lignes import lignes_plugin
    from cielircours.plugins.trous import trous_plugin

    for plugin in (trous_plugin, lignes_plugin):
        with pytest.raises(TypeError, match="Mode"):
            plugin(MarkdownIt(), "Trous")
