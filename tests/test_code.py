"""Code coloré et bloc terminal : deux rendus de blocs délimités (```)."""

import pytest

from cielircours.mdtext import Mode, rendre_corps
from outils import COURS_CSS, contraste, regle

CPP = "```cpp\n#include <iostream>\nint main() { return 0; }  // fin\n```\n"


@pytest.mark.parametrize("mode", [Mode.COMPLET, Mode.TROUS])
def test_un_bloc_cpp_est_colore(mode):
    html = rendre_corps(CPP, mode)
    assert html.startswith('<pre class="code"><code class="language-cpp">')
    assert '<span class="k">return</span>' in html  # mot-clé
    assert '<span class="cp">#include</span>' in html  # directive de préprocesseur
    assert '<span class="c1">// fin</span>' in html  # commentaire
    assert "&lt;iostream&gt;" in html  # le texte reste échappé


def test_le_texte_du_code_est_intact_apres_coloration():
    from html import unescape
    from re import sub

    source = 'if (a < b && c > "x\\"y") { s += \'z\'; } // <b>gras</b> & co\n'
    html = rendre_corps(f"```cpp\n{source}```\n", Mode.COMPLET)
    assert unescape(sub(r"<[^>]+>", "", html)).strip() == source.strip()
    assert "<b>" not in html


def test_un_bloc_terminal_est_style_terminal_sans_coloration():
    html = rendre_corps("```terminal\n$ g++ -o prog main.cpp\n$ ./prog\n```\n", Mode.COMPLET)
    assert html.startswith('<pre class="terminal"><code>')
    assert "<span" not in html
    assert "$ g++ -o prog main.cpp" in html


def test_le_terminal_echappe_son_contenu():
    html = rendre_corps("```terminal\n$ echo '<ins>x</ins>' > f & ls\n```\n", Mode.COMPLET)
    assert "&lt;ins&gt;x&lt;/ins&gt;" in html and "&amp; ls" in html
    assert "<ins" not in html


@pytest.mark.parametrize("info", ["", "text", "langage-inconnu"])
def test_langue_absente_ou_inconnue_ne_fait_pas_echouer(info):
    html = rendre_corps(f"```{info}\na < b\n```\n", Mode.COMPLET)
    assert "a &lt; b" in html and "<pre" in html


def test_les_mots_apres_la_langue_sont_ignores():
    assert 'class="language-cpp"' in rendre_corps("```cpp extra\nint x;\n```\n", Mode.COMPLET)


def test_ins_litteral_dans_un_bloc_colore_reste_litteral():
    for mode in Mode:
        html = rendre_corps("```cpp\n// <ins>x</ins>\n```\n", mode)
        assert "&lt;ins&gt;" in html and "<ins" not in html


def test_un_bloc_colore_dans_une_reponse_se_rend():
    html = rendre_corps(":::reponse 2\n```cpp\nint x;\n```\n:::\n", Mode.COMPLET)
    assert '<div class="reponse-bloc">' in html and '<span class="kt">int</span>' in html
    assert "reponse-bloc" not in rendre_corps(":::reponse 2\n```cpp\nint x;\n```\n:::\n", Mode.TROUS)
    assert "int x" not in rendre_corps(":::reponse 2\n```cpp\nint x;\n```\n:::\n", Mode.TROUS)


# ---------- feuille de style ----------

CLASSES_UTILISEES = ["k", "kt", "kd", "kn", "kr", "kc", "kp", "ow", "cp", "cpf", "c", "c1", "cm", "cs", "sd", "s", "s1", "s2", "sc", "se", "sa", "sb", "sh", "si", "sx", "m", "mi", "mf", "mh", "mo", "il"]


def _couleur(classe):
    import re

    m = re.search(r"color:\s*(#[0-9a-fA-F]{6})", regle(COURS_CSS.read_text(encoding="utf-8"), f"pre.code .{classe}"))
    return m.group(1) if m else None


def test_les_couleurs_du_code_restent_lisibles_sur_fond_blanc():
    colorees = {c: _couleur(c) for c in CLASSES_UTILISEES if _couleur(c)}
    assert {"k", "c1", "s", "mi", "cp"} <= set(colorees), colorees
    for classe, couleur in colorees.items():
        assert contraste(couleur, "#ffffff") >= 7, (classe, couleur)


def test_la_coloration_ne_repose_pas_sur_la_couleur_seule():
    css = COURS_CSS.read_text(encoding="utf-8")
    assert "font-weight: 700" in regle(css, "pre.code .k")  # mot-clé : gras
    assert "font-style: italic" in regle(css, "pre.code .c1")  # commentaire : italique
