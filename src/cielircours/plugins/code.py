"""Blocs de code : coloration syntaxique (Pygments) et bloc `terminal`.

- ```` ```cpp ```` : `<pre class="code">` dont les jetons portent les classes courtes de
  Pygments (`k`, `c1`…), que `cours.css` met en forme ;
- ```` ```terminal ```` : `<pre class="terminal">`, sans coloration (session de commandes) ;
- tout autre bloc, ou une langue que Pygments ne connaît pas : rendu par défaut, sans échec.

Le texte du code n'est jamais interprété : Pygments échappe tout, et un `<ins>` écrit dans un
bloc reste littéral (il n'est pas un trou).
"""

from markdown_it import MarkdownIt
from markdown_it.common.utils import escapeHtml
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name
from pygments.lexers.special import TextLexer
from pygments.util import ClassNotFound

TERMINAL = "terminal"


def _langue(info: str) -> str:
    mots = info.strip().split(None, 1)
    return mots[0] if mots else ""


def code_plugin(md: MarkdownIt) -> None:
    defaut = md.renderer.rules["fence"]
    formateur = HtmlFormatter(nowrap=True)

    def fence(tokens, idx, options, env):  # type: ignore[no-untyped-def]
        jeton = tokens[idx]
        langue = _langue(jeton.info)
        if langue.lower() == TERMINAL:
            return f'<pre class="terminal"><code>{escapeHtml(jeton.content)}</code></pre>\n'
        try:
            lexeur = get_lexer_by_name(langue, stripnl=False) if langue else None
        except ClassNotFound:
            lexeur = None
        if lexeur is None or isinstance(lexeur, TextLexer):
            return defaut(tokens, idx, options, env)
        corps = highlight(jeton.content, lexeur, formateur)
        return f'<pre class="code"><code class="language-{escapeHtml(langue)}">{corps}</code></pre>\n'

    md.renderer.rules["fence"] = fence
