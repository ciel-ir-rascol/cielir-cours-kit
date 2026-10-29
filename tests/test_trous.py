import pytest

from cielircours.mdtext import Mode, rendre_corps


def test_ins_devient_une_reponse_en_mode_complet():
    html = rendre_corps("Le hash fait <ins>40</ins> chiffres.", Mode.COMPLET)
    assert '<span class="reponse">40</span>' in html


def test_ins_devient_un_trou_calibre_en_mode_trous():
    html = rendre_corps("Le hash fait <ins>40</ins> chiffres.", Mode.TROUS)
    assert '<span class="trou" style="--car:2"></span>' in html
    assert "40" not in html


@pytest.mark.parametrize("mode", list(Mode))
@pytest.mark.parametrize(
    "source",
    [
        "a <ins>SECRET fin",
        "<ins>SECRET\n\nsuite</ins>",
        "<ins>\nSECRET\n</ins>",
        '<ins class="x">SECRET</ins>',
        "<INS>SECRET",
        "<ins>a <ins>b</ins> SECRET</ins>",
    ],
)
def test_ins_mal_forme_est_refuse(source, mode):
    with pytest.raises(ValueError, match="<ins"):
        rendre_corps(source, mode)


def test_erreur_ins_montre_le_fragment_fautif():
    with pytest.raises(ValueError, match="SECRET fin"):
        rendre_corps("a <ins>SECRET fin", Mode.TROUS)


def test_ins_dans_alt_ne_fuite_pas_en_mode_trous():
    html = rendre_corps("![<ins>SECRET</ins>](a.png)", Mode.TROUS)
    assert "SECRET" not in html


def test_ins_dans_alt_reste_lisible_en_mode_complet():
    html = rendre_corps("![<ins>SECRET</ins>](a.png)", Mode.COMPLET)
    assert 'alt="SECRET"' in html


@pytest.mark.parametrize(
    "source",
    [
        "- un item <ins>SECRET</ins>",
        "| a |\n|---|\n| <ins>SECRET</ins> |",
        "> [!NOTE]\n> voir <ins>SECRET</ins>",
        "[lien <ins>SECRET</ins>](http://x.y)",
        "**gras <ins>SECRET</ins>** et *<ins>SECRET</ins>*",
        "<ins>*SECRET*\nretour</ins>",
    ],
)
def test_ins_dans_les_structures_ne_fuite_pas_en_mode_trous(source):
    html = rendre_corps(source, Mode.TROUS)
    assert "SECRET" not in html and "retour" not in html
    assert 'class="trou"' in html


def test_ins_dans_les_structures_rendu_en_mode_complet():
    html = rendre_corps("- item <ins>SECRET</ins>", Mode.COMPLET)
    assert '<li>item <span class="reponse">SECRET</span></li>' in html


def test_ins_dans_un_code_span_reste_litteral():
    html = rendre_corps("écrire `<ins>x</ins>` ici", Mode.TROUS)
    assert "&lt;ins&gt;x" in html


def test_car_compte_le_texte_brut_sans_balisage():
    html = rendre_corps("<ins>*ab* `cd`</ins>", Mode.TROUS)
    assert 'style="--car:5"' in html


def test_mode_inattendu_est_refuse():
    from cielircours.mdtext import construire_markdown

    with pytest.raises(TypeError, match="Mode"):
        construire_markdown("Trous")


@pytest.mark.parametrize("mode", list(Mode))
@pytest.mark.parametrize(
    "source",
    [
        '[x](http://u "<ins>SECRET</ins>")',
        '![i](a.png "<ins>SECRET</ins>")',
        '[r]: http://u "<ins>SECRET</ins>"\n\nvoir [r]',
        "```<ins>SECRET</ins>\ncode\n```",
    ],
)
def test_ins_dans_un_attribut_est_refuse(source, mode):
    with pytest.raises(ValueError, match="attribut|bloc de code"):
        rendre_corps(source, mode)


def test_erreur_attribut_montre_le_fragment_fautif():
    with pytest.raises(ValueError, match="SECRET"):
        rendre_corps('[x](http://u "<ins>SECRET</ins>")', Mode.TROUS)


@pytest.mark.parametrize("mode", list(Mode))
def test_ins_litteral_dans_code_span_et_bloc_de_code_passe(mode):
    html = rendre_corps("`<ins>x</ins>`\n\n```\n<ins>y</ins>\n```\n", mode)
    assert "&lt;ins&gt;x" in html and "&lt;ins&gt;y" in html
