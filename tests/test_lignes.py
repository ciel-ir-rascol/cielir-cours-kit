"""Réponses rédigées : `<ins lignes="n">…</ins>`, la forme longue du trou."""

import pytest

from cielircours.mdtext import Mode, rendre_corps

SOURCE = '<ins lignes="3">Parce que c\'est distribué.</ins>'


def test_lignes_en_mode_trous_ne_laissent_pas_la_reponse():
    html = rendre_corps(SOURCE, Mode.TROUS)
    assert '<div class="lignes" style="--n:3"></div>' in html
    assert "distribué" not in html and "<p>" not in html


def test_lignes_en_mode_complet_rendent_la_reponse():
    html = rendre_corps(SOURCE, Mode.COMPLET)
    assert html == '<div class="reponse-bloc">\n<p>Parce que c\'est distribué.</p>\n</div>\n'


def test_la_reponse_peut_courir_sur_plusieurs_lignes_de_source_et_porter_du_balisage():
    src = '<ins lignes="2">**secret** et `code`\nsuite</ins>'
    html = rendre_corps(src, Mode.COMPLET)
    assert "<strong>secret</strong>" in html and "<code>code</code>" in html and "suite" in html
    assert "secret" not in rendre_corps(src, Mode.TROUS) and "suite" not in rendre_corps(src, Mode.TROUS)


@pytest.mark.parametrize("valeur", ["0", "x", "-1", "", "2 3", "1.5"])
@pytest.mark.parametrize("mode", list(Mode))
def test_nombre_de_lignes_invalide_est_refuse(valeur, mode):
    with pytest.raises(ValueError, match="nombre de lignes"):
        rendre_corps(f'<ins lignes="{valeur}">secret</ins>', mode)


@pytest.mark.parametrize(
    "source",
    [
        '<ins lignes="2">SECRET',                                     # non appariée
        '<ins lignes="2">SECRET</ins> et du texte',                    # pas seule dans son paragraphe
        'du texte <ins lignes="2">SECRET</ins>',
        '<ins lignes="2">SECRET\n\nsuite</ins>',                       # à cheval sur deux paragraphes
        '<ins lignes="2">a <ins>b</ins> SECRET</ins>',                 # imbriquée avec un trou court
        '<ins lignes="2">a <ins lignes="1">b</ins> SECRET</ins>',      # imbriquée
        '<ins lignes="2">SECRET</ins></ins>',                          # fermeture en trop
        '<ins lignes="2">SECRET</ins> <ins lignes="1">AUTRE</ins>',    # deux dans un paragraphe
        '<ins lignes="2">\nSECRET\n</ins>',                            # seule sur sa ligne : html_block
        '<ins lignes="2">\n\nSECRET\n\n</ins>',
        '| a |\n|---|\n| <ins lignes="2">SECRET</ins> |',             # dans un tableau
        '# titre <ins lignes="2">SECRET</ins>',                        # dans un titre
        '<ins lignes=2>SECRET</ins>',                                  # guillemets absents
        '<ins lignes="2" class="x">SECRET</ins>',                      # autre attribut
        '[x](http://u "<ins lignes=\\"2\\">SECRET</ins>")',            # dans un attribut
        '![<ins lignes="2">SECRET</ins>](a.png)',                      # dans un alt
    ],
)
@pytest.mark.parametrize("mode", list(Mode))
def test_forme_longue_mal_formee_ne_fuite_jamais(source, mode):
    try:
        html = rendre_corps(source, mode)
    except ValueError:
        return
    assert mode is Mode.COMPLET and "<ins" not in html, html  # jamais de réponse en mode trous
    # (le mode complet peut tout montrer, mais jamais de balise brute)


@pytest.mark.parametrize(
    "source",
    [
        '<ins lignes="2">SECRET',
        '<ins lignes="2">SECRET</ins> et du texte',
        '<ins lignes="2">\nSECRET\n</ins>',
        '| a |\n|---|\n| <ins lignes="2">SECRET</ins> |',
        '<ins lignes="2">a <ins>b</ins> SECRET</ins>',
        '<ins lignes="2">SECRET\n\nsuite</ins>',
    ],
)
def test_forme_longue_mal_formee_est_refusee_en_mode_trous(source):
    with pytest.raises(ValueError, match="<ins"):
        rendre_corps(source, Mode.TROUS)


@pytest.mark.parametrize(
    "src",
    [
        ":::reponse 3\nSECRETX\n:::",
        ":::reponse\nSECRETX\n:::",
        ":::reponse3\nSECRETX\n:::",
        "a\n:::reponse 2\nSECRETX\n:::",              # collée à un paragraphe
        "a\n\n:::REPONSE 2\nSECRETX\n:::",             # casse
        "  :::Reponse 2\nSECRETX\n:::",
        "- item\n\n  :::reponse 2\n  SECRETX\n  :::",   # dans une liste
        "> :::reponse 2\n> SECRETX\n> :::",             # dans une citation
        "> [!NOTE]\n> :::reponse 2\n> SECRETX\n> :::",
        "::: reponse 2\nSECRETX\n:::",
        "```\n:::reponse 2\n```",                       # même dans un bloc de code : refusé
    ],
)
@pytest.mark.parametrize("mode", list(Mode))
def test_ancienne_syntaxe_est_refusee_ou_qu_elle_soit(src, mode):
    with pytest.raises(ValueError, match="ins lignes"):
        rendre_corps(src, mode)


def test_un_mot_qui_contient_la_syntaxe_au_milieu_d_une_ligne_n_est_pas_refuse():
    assert "reponse" in rendre_corps("la syntaxe :::reponse est partie", Mode.COMPLET)


@pytest.mark.parametrize("valeur", ["31", "100000", "99999999999999999999", "٢", "²", "１", "٣٠"])
@pytest.mark.parametrize("mode", list(Mode))
def test_valeur_hors_borne_ou_non_ascii_est_refusee_proprement(valeur, mode):
    with pytest.raises(ValueError, match=r"nombre de lignes|borne"):
        rendre_corps(f'<ins lignes="{valeur}">secret</ins>', mode)


def test_la_borne_est_incluse_et_le_message_la_donne():
    assert "--n:30" in rendre_corps('<ins lignes="30">x</ins>', Mode.TROUS)
    with pytest.raises(ValueError, match=r"'31'.*30"):
        rendre_corps('<ins lignes="31">x</ins>', Mode.TROUS)


def test_le_trou_court_n_est_pas_touche():
    html = rendre_corps("Le hash fait <ins>40</ins> chiffres.", Mode.COMPLET)
    assert '<span class="reponse">40</span>' in html
    assert "reponse-bloc" not in html


def test_reponse_longue_dans_une_liste_ne_fuite_pas():
    html = rendre_corps('- item\n\n  <ins lignes="2">secret</ins>', Mode.TROUS)
    assert "secret" not in html and 'class="lignes" style="--n:2"' in html


def test_deux_reponses_longues_et_texte_entre_les_deux():
    src = '<ins lignes="1">**secret**</ins>\n\ntexte\n\n<ins lignes="4">autre</ins>'
    html = rendre_corps(src, Mode.TROUS)
    assert "secret" not in html and "autre" not in html and "texte" in html
    assert "--n:1" in html and "--n:4" in html


def test_greffons_refusent_un_mode_inattendu():
    from markdown_it import MarkdownIt

    from cielircours.plugins.code import code_plugin
    from cielircours.plugins.lignes import lignes_plugin
    from cielircours.plugins.trous import trous_plugin

    for plugin in (trous_plugin, lignes_plugin, code_plugin):
        with pytest.raises(TypeError, match="Mode"):
            plugin(MarkdownIt(), "Trous")
