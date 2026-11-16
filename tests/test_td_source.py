"""Préparation de la source d'un TD : contrôles, numérotation, réponses."""

from pathlib import Path

import pytest

from cielircours.config import lire_td
from cielircours.td import Exemplaire, preparer_source

TD = lire_td(Path(__file__).parent / "data" / "td.yml")
REP = '<div class="reponse">\n\n{}\n\n</div>'


def _q(texte: str, reponse: str | None = "R") -> str:
    bloc = f"**Q.** {texte}"
    return bloc if reponse is None else f"{bloc}\n\n{REP.format(reponse)}"


def corrige(source: str) -> str:
    return preparer_source(source, TD, Exemplaire.CORRIGE)


def sujet(source: str) -> str:
    return preparer_source(source, TD, Exemplaire.SUJET)


def test_questions_numerotees_en_continu():
    source = f"## A\n\n{_q('un')}\n\n{_q('deux')}\n\n## B\n\n{_q('trois')}\n"
    sortie = corrige(source)
    assert "**Q1.** un" in sortie and "**Q2.** deux" in sortie and "**Q3.** trois" in sortie
    assert "**Q.**" not in sortie


def test_question_dans_le_code_ignoree():
    source = f"```markdown\n**Q.** exemple\n```\n\n{_q('vraie')}\n"
    sortie = corrige(source)
    assert "**Q.** exemple" in sortie
    assert "**Q1.** vraie" in sortie


def test_reponse_retiree_du_sujet_gardee_au_corrige():
    source = _q("Combien ?", "SECRET") + "\n"
    assert "SECRET" not in sujet(source)
    assert "**Q1.** Combien ?" in sujet(source)
    assert "SECRET" in corrige(source)


def test_reponse_sans_question():
    with pytest.raises(ValueError, match="ne suit aucune question"):
        corrige("Texte.\n\n" + REP.format("R") + "\n")


def test_deux_reponses_pour_une_question():
    with pytest.raises(ValueError, match="ne suit aucune question"):
        corrige(_q("un") + "\n\n" + REP.format("R2") + "\n")


def test_question_sans_reponse_refusee():
    with pytest.raises(ValueError, match="Q2"):
        corrige(f"{_q('un')}\n\n{_q('deux', None)}\n\n{_q('trois')}\n")


def test_question_sur_un_dr_sans_reponse_acceptee():
    sortie = corrige(_q("Compléter le DR1.", None) + "\n")
    assert "**Q1.** Compléter le DR1." in sortie


def test_question_sur_plusieurs_blocs():
    source = "**Q.** Soit :\n\n- a\n- b\n\n```cpp\nint x;\n```\n\n" + REP.format("R") + "\n"
    assert "**Q1.** Soit :" in corrige(source)


def test_dt_dr_numerotes():
    source = ('<div class="dt" titre="Badge">\n\nX\n\n</div>\n\n'
              '<div class="dt" titre="Tests">\n\nY\n\n</div>\n\n'
              '<div class="dr" titre="Relations">\n\nZ\n\n</div>\n')
    sortie = corrige(source)
    assert '<div class="dt"><p class="bloc-titre">DT1 - Badge</p>' in sortie
    assert '<div class="dt"><p class="bloc-titre">DT2 - Tests</p>' in sortie
    assert ('<div class="dr"><p class="bloc-titre">DR1 - Relations</p>'
            '<p class="dr-nom">Nom : ……………… — à rendre avec la copie</p>') in sortie


def test_ressource():
    sortie = corrige('<div class="ressource" titre="La visibilité">\n\nTexte\n\n</div>\n')
    assert '<div class="ressource"><p class="bloc-titre">Ressource - La visibilité</p>' in sortie


def test_bloc_sans_titre_refuse():
    with pytest.raises(ValueError, match="titre"):
        corrige('<div class="dt">\n\nX\n\n</div>\n')


def test_bandeau_de_partie():
    sortie = corrige('## A\n\n<p class="partie" duree="20 min" niveau="2"></p>\n')
    assert ('<p class="partie"><span class="duree">20 min</span> '
            '<span class="niveau">★★☆☆</span></p>') in sortie


def test_bandeau_sans_niveau():
    sortie = corrige('<p class="partie" duree="20 min"></p>\n')
    assert '<p class="partie"><span class="duree">20 min</span></p>' in sortie


@pytest.mark.parametrize("niveau", ["0", "5", "x"])
def test_bandeau_niveau_invalide(niveau):
    with pytest.raises(ValueError, match="niveau"):
        corrige(f'<p class="partie" duree="20 min" niveau="{niveau}"></p>\n')


@pytest.mark.parametrize("interdit", ["Le <ins>trou</ins>.", '<div class="ecran">\n\nX\n\n</div>',
                                      'Une <span class="papier">incise</span>.'])
def test_ins_et_supports_refuses(interdit):
    with pytest.raises(ValueError, match="pas dans un TD"):
        corrige(interdit + "\n")


def test_ins_dans_le_code_tolere():
    assert "<ins>" in corrige("```html\n<ins>x</ins>\n```\n")


def test_titre_niveau_1():
    assert "# TD01" not in corrige("# TD01 - Diagramme de classes UML\n\nTexte.\n")
    with pytest.raises(ValueError, match="TD01 - Diagramme de classes UML"):
        corrige("# TD02 - Autre\n\nTexte.\n")


@pytest.mark.parametrize("bloc", ['<div class="reponse">SECRET</div>',
                                  '> <div class="reponse">\n>\n> SECRET\n>\n> </div>'])
def test_trace_de_reponse_refusee_au_sujet(bloc):
    with pytest.raises(ValueError, match="réponse"):
        sujet(f"**Q.** Compléter le DR1.\n\n{bloc}\n")


def test_reponse_avec_attribut_retiree_du_sujet():
    source = '**Q.** Compléter le DR1.\n\n<div class="reponse" data-x="a">\n\nSECRET\n\n</div>\n'
    assert "SECRET" not in sujet(source)


def test_source_du_depot_sujet_sans_reponses():
    source = "**Q.** Combien ?\n\n**Q.** Pourquoi ?\n"
    sortie = preparer_source(source, TD, Exemplaire.SUJET, source_corrigee=False)
    assert "**Q1.** Combien ?" in sortie and "**Q2.** Pourquoi ?" in sortie
