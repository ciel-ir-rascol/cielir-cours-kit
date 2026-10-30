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
@pytest.mark.parametrize("langue", ["terminal", "cpp", "python", "langage-inconnu", ""])
def test_un_trou_mal_forme_dans_un_bloc_est_refuse(contenu, mode, langue):
    with pytest.raises(ValueError, match="<ins.*bloc"):
        rendre_corps(f"```{langue}\n{contenu}\n```\n", mode)


@pytest.mark.parametrize("langue", ["terminal", "cpp", ""])
def test_un_trou_mal_forme_dans_un_bloc_montre_le_fragment_fautif(langue):
    with pytest.raises(ValueError, match="SECRET"):
        rendre_corps(f"```{langue}\n$ a <ins>SECRET fin\n```\n", Mode.TROUS)


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


# ---------- trous dans tous les blocs de code ----------

BLOCS = ["cpp", "python", "bash", "langage-inconnu", "", "terminal"]


def _bloc(langue, contenu):
    return f"```{langue}\n{contenu}\n```\n"


@pytest.mark.parametrize("langue", BLOCS)
def test_un_trou_dans_un_bloc_est_la_reponse_en_mode_complet(langue):
    html = rendre_corps(_bloc(langue, "float notes[<ins>5</ins>];"), Mode.COMPLET)
    assert '<span class="reponse">5</span>' in html and "<ins" not in html


@pytest.mark.parametrize("langue", BLOCS)
def test_un_trou_dans_un_bloc_est_un_blanc_en_mode_trous(langue):
    html = rendre_corps(_bloc(langue, "float notes[<ins>5</ins>];"), Mode.TROUS)
    assert '<span class="trou" style="--car:1"></span>' in html
    assert "reponse" not in html


def test_la_coloration_reste_juste_autour_du_trou():
    html = rendre_corps(_bloc("cpp", "float notes[<ins>5</ins>];"), Mode.COMPLET)
    assert '<span class="kt">float</span>' in html
    assert 'notes' in html and '<span class="reponse">5</span>' in html
    assert "CielirTrou" not in html


@pytest.mark.parametrize(
    ("langue", "source"),
    [
        ("cpp", 'cout << "Bonjour <ins>SECRETX</ins> !";'),                 # dans une chaîne
        ("cpp", "// la variable <ins>SECRETX</ins> vaut 5"),                 # dans un commentaire
        ("cpp", "/* bloc <ins>SECRETX</ins>\n   suite */"),                  # dans un commentaire multiligne
        ("cpp", "#include <ins>SECRETX</ins>"),                              # directive
        ("cpp", "#include <<ins>SECRETX</ins>>"),
        ("cpp", "#define <ins>SECRETX</ins> 22"),                            # macro
        ("cpp", "<ins>SECRETX</ins> x = 1;"),                                # en début de bloc
        ("cpp", "int x = <ins>SECRETX</ins>"),                               # en fin de bloc
        ("cpp", "int <ins>SECRETX</ins> = <ins>SECRETY</ins>;"),             # deux trous sur une ligne
        ("cpp", "int x;\n<ins>SECRETX</ins>\nint y;"),                       # seul sur sa ligne
        ("cpp", "int x = 0.<ins>SECRETX</ins>;"),                            # collé à un nombre
        ("cpp", "int t[<ins>SECRETX</ins>] = {1, 2};"),
        ("python", 'print("<ins>SECRETX</ins>")  # <ins>SECRETY</ins>'),
        ("python", 'x = """a\n<ins>SECRETX</ins>\nb"""'),                   # chaîne multiligne
        ("bash", "echo $<ins>SECRETX</ins> 'a'"),
        ("html", '<a href="<ins>SECRETX</ins>">t</a>'),
        ("json", '{"k": "<ins>SECRETX</ins>"}'),
        ("langage-inconnu", "a <ins>SECRETX</ins> b"),
        ("", "a <ins>SECRETX</ins> b"),
    ],
)
def test_un_trou_traverse_la_coloration_dans_tous_les_contextes(langue, source):
    complet = rendre_corps(_bloc(langue, source), Mode.COMPLET)
    assert complet.count('class="reponse"') == source.count("<ins>")
    assert "CielirTrou" not in complet and "<ins" not in complet
    trous = rendre_corps(_bloc(langue, source), Mode.TROUS)
    assert "SECRET" not in trous and "CielirTrou" not in trous and "<ins" not in trous
    assert trous.count('class="trou"') == source.count("<ins>")


def test_le_texte_autour_des_trous_est_intact_apres_coloration():
    from html import unescape
    from re import sub

    source = 'if (a < b && c > "x<ins>REP</ins>y") { s += \'z\'; } // <ins>AUTRE</ins> & co'
    html = rendre_corps(_bloc("cpp", source), Mode.COMPLET)
    assert unescape(sub(r"<[^>]+>", "", html)).strip() == source.replace("<ins>", "").replace("</ins>", "")


def test_une_sentinelle_ecrite_a_la_main_n_est_pas_un_trou():
    ecrit = "CielirTrouSentinelleaaaa"
    source = f"int {ecrit} = <ins>5</ins>;"
    html = rendre_corps(_bloc("cpp", source), Mode.COMPLET)
    assert ecrit in html and html.count('class="reponse"') == 1
    html = rendre_corps(_bloc("cpp", f"int {ecrit} = 3;\nint {ecrit}X = <ins>5</ins>;"), Mode.TROUS)
    assert ecrit in html and html.count('class="trou"') == 1


def test_les_lettres_de_la_sentinelle_ne_se_prefixent_pas_et_plus_de_26_trous_passent():
    source = " ".join(f"<ins>r{n}</ins>" for n in range(60))
    html = rendre_corps(_bloc("cpp", source), Mode.COMPLET)
    assert html.count('class="reponse"') == 60
    for n in range(60):
        assert f">r{n}</span>" in html


def test_un_lexeur_qui_decoupe_la_sentinelle_leve_une_erreur(monkeypatch):
    """Garde-fou : si la coloration perd ou découpe un trou, la génération échoue."""
    import cielircours.plugins.code as code

    reel = code.highlight
    monkeypatch.setattr(code, "highlight", lambda t, l, f: reel(t, l, f).replace("CielirTrouSentinelle", "Ciel</span><span>irTrouSentinelle", 1))
    with pytest.raises(ValueError, match="découpé ou perdu"):
        rendre_corps(_bloc("cpp", "int x = <ins>5</ins>;"), Mode.TROUS)


def test_un_lexeur_qui_perd_la_sentinelle_leve_une_erreur(monkeypatch):
    import cielircours.plugins.code as code

    monkeypatch.setattr(code, "highlight", lambda t, l, f: "<span>rien</span>")
    for mode in Mode:
        with pytest.raises(ValueError, match="découpé ou perdu"):
            rendre_corps(_bloc("cpp", "int x = <ins>5</ins>;"), mode)


def test_un_lexeur_qui_duplique_la_sentinelle_leve_une_erreur(monkeypatch):
    import cielircours.plugins.code as code

    reel = code.highlight
    monkeypatch.setattr(code, "highlight", lambda t, l, f: reel(t, l, f) + reel(t, l, f))
    with pytest.raises(ValueError, match="découpé ou perdu"):
        rendre_corps(_bloc("cpp", "int x = <ins>5</ins>;"), Mode.TROUS)


def test_un_bloc_sans_trou_reste_rendu_comme_avant():
    assert rendre_corps(CPP, Mode.COMPLET) == rendre_corps(CPP, Mode.TROUS)
    assert rendre_corps("```\na < b\n```\n", Mode.COMPLET).startswith("<pre><code>a &lt; b")
