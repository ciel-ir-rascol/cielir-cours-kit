"""Blocs de code : coloration syntaxique (Pygments) et bloc `terminal`.

- ```` ```cpp ```` : `<pre class="code">` dont les jetons portent les classes courtes de
  Pygments (`k`, `c1`…), que `cours.css` met en forme ;
- ```` ```terminal ```` : `<pre class="terminal">`, sans coloration (session de commandes) ;
  c'est le seul bloc où `<ins>réponse</ins>` est un trou, comme dans le texte courant : un cours
  de ligne de commande à compléter en vit ;
- tout autre bloc, ou une langue que Pygments ne connaît pas : rendu par défaut, sans échec.

Le texte du code n'est jamais interprété : tout est échappé, et un `<ins>` écrit dans un bloc
d'un autre langage reste littéral (il n'est pas un trou). Seule balise reconnue, dans un bloc
`terminal` : `<ins>`. Le contenu sort échappé, donc le garde-fou après rendu (`mdtext.py`) ne
voit pas un `<ins>` resté en clair : c'est ici qu'un trou mal formé (non apparié, imbriqué, avec
attribut, sur plusieurs lignes) est refusé, faute de quoi sa réponse s'afficherait dans le
document à trous.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from markdown_it import MarkdownIt
from markdown_it.common.utils import escapeHtml
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name
from pygments.lexers.special import TextLexer
from pygments.util import ClassNotFound

if TYPE_CHECKING:
    from cielircours.mdtext import Mode

TERMINAL = "terminal"


def _langue(info: str) -> str:
    mots = info.strip().split(None, 1)
    return mots[0] if mots else ""


_BALISE_INS = re.compile(r"</?ins\b", re.IGNORECASE)
_TROU = re.compile(r"<ins>(.*?)</ins>", re.IGNORECASE)


def _fragment(contenu: str, debut: int) -> str:
    return contenu[max(0, debut - 30) : debut + 60].replace("\n", " ")


def _terminal(contenu: str, mode: Mode) -> str:
    """Contenu d'un bloc terminal : texte échappé, `<ins>x</ins>` devenu trou ou réponse."""
    from cielircours.mdtext import Mode  # import tardif : mdtext importe ce module

    trous = list(_TROU.finditer(contenu))
    balises = list(_BALISE_INS.finditer(contenu))
    if len(balises) != 2 * len(trous) or any("\n" in t.group(1) for t in trous):
        # toute balise `<ins` qui n'appartient pas à une paire `<ins>…</ins>` sur une seule
        # ligne : non appariée, imbriquée, avec attribut, à cheval sur deux lignes
        propres = {t.start() for t in trous} | {t.end() - len("</ins>") for t in trous}
        fautive = next((m for m in balises if m.start() not in propres), None)
        debut = fautive.start() if fautive else trous[0].start()
        raise ValueError(
            "balise <ins> mal formée dans un bloc terminal (non appariée, avec attribut, "
            f"imbriquée ou sur plusieurs lignes) : …{_fragment(contenu, debut)}…"
        )
    morceaux: list[str] = []
    fin = 0
    for t in trous:
        morceaux.append(escapeHtml(contenu[fin : t.start()]))
        reponse = t.group(1)
        if mode is Mode.TROUS:
            morceaux.append(f'<span class="trou" style="--car:{len(reponse.strip())}"></span>')
        else:
            morceaux.append(f'<span class="reponse">{escapeHtml(reponse)}</span>')
        fin = t.end()
    morceaux.append(escapeHtml(contenu[fin:]))
    return "".join(morceaux)


def code_plugin(md: MarkdownIt, mode: Mode) -> None:
    from cielircours.mdtext import Mode

    if not isinstance(mode, Mode):
        raise TypeError(f"mode attendu : un Mode, reçu {mode!r}")
    defaut = md.renderer.rules["fence"]
    formateur = HtmlFormatter(nowrap=True)

    def fence(tokens, idx, options, env):  # type: ignore[no-untyped-def]
        jeton = tokens[idx]
        langue = _langue(jeton.info)
        if langue.lower() == TERMINAL:
            return f'<pre class="terminal"><code>{_terminal(jeton.content, mode)}</code></pre>\n'
        try:
            lexeur = get_lexer_by_name(langue, stripnl=False) if langue else None
        except ClassNotFound:
            lexeur = None
        if lexeur is None or isinstance(lexeur, TextLexer):
            return defaut(tokens, idx, options, env)
        corps = highlight(jeton.content, lexeur, formateur)
        return f'<pre class="code"><code class="language-{escapeHtml(langue)}">{corps}</code></pre>\n'

    md.renderer.rules["fence"] = fence
