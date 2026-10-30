"""Une phrase d'amorce reste avec le tableau, la figure ou le bloc de code qu'elle annonce."""

import pytest

from cielircours.mdtext import Mode, rendre_corps

TABLEAU = "| a | b |\n| --- | --- |\n| 1 | 2 |"


@pytest.mark.parametrize("mode", list(Mode))
@pytest.mark.parametrize(
    "suite",
    [
        TABLEAU,
        "```cpp\nint x;\n```",
        "```terminal\n$ ls\n```",
        "    code indenté",
        "![schéma](img/s.svg)",
        "<figure><img src=\"x.png\"></figure>",
    ],
)
def test_le_paragraphe_qui_annonce_est_marque(suite, mode):
    html = rendre_corps(f"Retrouvez les noms :\n\n{suite}\n", mode)
    assert html.startswith('<p class="amorce">Retrouvez les noms :</p>')


@pytest.mark.parametrize(
    "source",
    [
        "Un paragraphe.\n\nUn autre.",
        "Texte.\n\n- liste",
        "Texte.\n\n> citation",
        "Texte.\n\n## Titre",
        "Texte avec ![img](a.png) dans la ligne.\n\nautre",
        f"Texte.\n\nSuite.\n\n{TABLEAU}",
    ],
)
def test_un_paragraphe_ordinaire_n_est_pas_marque_sauf_celui_qui_precede_le_bloc(source):
    html = rendre_corps(source, Mode.COMPLET)
    assert html.count("amorce") == (1 if "Suite." in source else 0)
    if "Suite." in source:
        assert '<p>Texte.</p>' in html and '<p class="amorce">Suite.</p>' in html


def test_un_tableau_precede_d_un_titre_n_ajoute_rien():
    assert "amorce" not in rendre_corps(f"## Titre\n\n{TABLEAU}\n", Mode.COMPLET)


def test_la_regle_css_existe():
    from outils import COURS_CSS, regle

    assert "break-after: avoid" in regle(COURS_CSS.read_text(encoding="utf-8"), "p.amorce")


def _p(html):
    return html.split("</p>")[0]


@pytest.mark.parametrize("mode", list(Mode))
@pytest.mark.parametrize(
    ("nom", "suite"),
    [
        ("figure", '<figure><img src="x.png" alt=""><figcaption>légende</figcaption></figure>'),
        ("image seule", '![schéma](img/s.svg "titre")'),
        ("bloc de code", "```cpp\nint x;\n```"),
        ("bloc terminal", "```terminal\n$ ls\n```"),
    ],
)
def test_chaque_bloc_annonce_marque_son_amorce_et_pas_le_paragraphe_d_avant(nom, suite, mode):
    html = rendre_corps(f"Premier.\n\nConsigne.\n\n{suite}\n", mode)
    assert '<p>Premier.</p>' in html, nom
    assert '<p class="amorce">Consigne.</p>' in html, nom
