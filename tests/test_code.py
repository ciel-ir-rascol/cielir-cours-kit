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
    html = rendre_corps("```terminal\n$ echo '<script>x</script>' > f & ls\n```\n", Mode.COMPLET)
    assert "&lt;script&gt;x&lt;/script&gt;" in html and "&amp; ls" in html
    assert "<script" not in html


def test_un_trou_dans_un_terminal_est_la_reponse_en_mode_complet():
    html = rendre_corps("```terminal\n$ g++ -o <ins>age</ins> age.cpp\n```\n", Mode.COMPLET)
    assert html == '<pre class="terminal"><code>$ g++ -o <span class="reponse">age</span> age.cpp\n</code></pre>\n'


def test_un_trou_dans_un_terminal_est_un_blanc_calibre_en_mode_trous():
    html = rendre_corps("```terminal\n$ g++ -o <ins>age</ins> age.cpp\n```\n", Mode.TROUS)
    assert html == '<pre class="terminal"><code>$ g++ -o <span class="trou" style="--car:3"></span> age.cpp\n</code></pre>\n'
    assert "age</span>" not in html


def test_la_reponse_d_un_trou_de_terminal_reste_echappee():
    html = rendre_corps("```terminal\n$ <ins>a < b & <i>c</i></ins>\n```\n", Mode.COMPLET)
    assert '<span class="reponse">a &lt; b &amp; &lt;i&gt;c&lt;/i&gt;</span>' in html


def test_plusieurs_trous_sur_une_ligne_et_sur_plusieurs_lignes():
    src = "```terminal\n<ins>git</ins> add <ins>f.txt</ins>\n<ins>git</ins> commit\n```\n"
    html = rendre_corps(src, Mode.TROUS)
    assert html.count('class="trou"') == 3 and "--car:5" in html
    for secret in ("git</", "f.txt</"):
        assert secret not in html


@pytest.mark.parametrize(
    "contenu",
    [
        "$ a <ins>SECRET fin",
        "$ a SECRET</ins> fin",
        "$ <ins>a <ins>b</ins> SECRET</ins>",
        '$ <ins class="x">SECRET</ins>',
        '$ <ins lignes="2">SECRET</ins>',
        "$ <ins>SECRET\nsuite</ins>",
        "$ <INS>SECRET",
        "$ <ins SECRET",
    ],
)
@pytest.mark.parametrize("mode", list(Mode))
def test_un_trou_mal_forme_dans_un_terminal_est_refuse(contenu, mode):
    with pytest.raises(ValueError, match="<ins.*terminal"):
        rendre_corps(f"```terminal\n{contenu}\n```\n", mode)


def test_un_trou_mal_forme_dans_un_terminal_montre_le_fragment_fautif():
    with pytest.raises(ValueError, match="SECRET"):
        rendre_corps("```terminal\n$ a <ins>SECRET fin\n```\n", Mode.TROUS)


@pytest.mark.parametrize("langue", ["bash", "cpp", "", "text", "sh"])
@pytest.mark.parametrize("mode", list(Mode))
def test_hors_terminal_ins_reste_litteral_meme_mal_forme(langue, mode):
    html = rendre_corps(f"```{langue}\n# <ins>SECRET fin\n```\n", mode)
    assert "&lt;ins&gt;SECRET" in html and "<ins" not in html


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


def test_un_code_en_ligne_dans_une_reponse_se_rend():
    html = rendre_corps('<ins lignes="2">`int x;`</ins>\n', Mode.COMPLET)
    assert '<div class="reponse-bloc">' in html and "<code>int x;</code>" in html
    assert "int x" not in rendre_corps('<ins lignes="2">`int x;`</ins>\n', Mode.TROUS)


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
