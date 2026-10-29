import pytest
from markdown_it import MarkdownIt

from cielircours.plugins.alertes import alertes_plugin


def rendre(source: str) -> str:
    md = MarkdownIt("commonmark")
    alertes_plugin(md)
    return md.render(source)


def test_note_devient_un_aside_titre():
    html = rendre("> [!NOTE]\n> Verrouiller plutôt que supprimer.")
    assert '<aside class="alerte alerte--note">' in html
    assert '<p class="alerte__titre">Note</p>' in html
    assert "Verrouiller plutôt que supprimer." in html
    assert "</aside>" in html
    assert "<blockquote>" not in html


@pytest.mark.parametrize(
    "marqueur, classe, titre",
    [
        ("NOTE", "note", "Note"),
        ("TIP", "astuce", "Astuce"),
        ("IMPORTANT", "important", "Important"),
        ("WARNING", "attention", "Attention"),
        ("CAUTION", "danger", "Danger"),
    ],
)
def test_correspondance_des_types(marqueur, classe, titre):
    html = rendre(f"> [!{marqueur}]\n> Texte.")
    assert f'<aside class="alerte alerte--{classe}">' in html
    assert f'<p class="alerte__titre">{titre}</p>' in html


def test_le_marqueur_disparait_de_la_sortie():
    html = rendre("> [!WARNING]\n> Attention au piège.")
    assert "[!WARNING]" not in html
    assert "Attention au piège." in html


def test_marqueur_seul_sur_sa_ligne_ne_laisse_pas_de_paragraphe_vide():
    html = rendre("> [!NOTE]\n> Corps.")
    assert "<p></p>" not in html
    assert "<p>Corps.</p>" in html


def test_le_type_est_insensible_a_la_casse():
    assert 'alerte--note">' in rendre("> [!note]\n> x")


def test_contenu_multi_paragraphes_et_inline_conserves():
    html = rendre("> [!TIP]\n> Un **gras**.\n>\n> Second paragraphe.")
    assert '<aside class="alerte alerte--astuce">' in html
    assert "<strong>gras</strong>" in html
    assert "<p>Second paragraphe.</p>" in html
    assert html.count("</aside>") == 1


def test_citation_ordinaire_reste_un_blockquote():
    assert "<blockquote>" in rendre("> Une citation simple.")


def test_type_inconnu_reste_un_blockquote():
    html = rendre("> [!TRUC]\n> x")
    assert "<blockquote>" in html
    assert "<aside" not in html


def test_alertes_imbriquees_dans_une_citation_ordinaire():
    html = rendre("> citation\n>\n> > [!NOTE]\n> > interne")
    assert html.count("<blockquote>") == 1
    assert '<aside class="alerte alerte--note">' in html
    assert html.count("</aside>") == 1
