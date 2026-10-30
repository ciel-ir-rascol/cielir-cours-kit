"""Blocs de code : coloration syntaxique (Pygments), bloc `terminal`, et trous dans tous les blocs.

- ```` ```cpp ```` : `<pre class="code">` dont les jetons portent les classes courtes de
  Pygments (`k`, `c1`…), que `cours.css` met en forme ;
- ```` ```terminal ```` : `<pre class="terminal">`, sans coloration (session de commandes) ;
- tout autre bloc, ou une langue que Pygments ne connaît pas : rendu par défaut, sans échec.

**Dans tout bloc, quelle que soit sa langue**, `<ins>réponse</ins>` est un trou, comme dans le
texte courant : la réponse en mode complet, un blanc calibré en mode trous. Le reste du bloc
garde sa coloration. Le code en ligne (`` `…` ``) reste littéral.

Le texte du code n'est jamais interprété : tout est échappé, `<ins>` est la seule balise reconnue.
Le contenu sort échappé, donc le garde-fou après rendu (`mdtext.py`) ne voit pas un `<ins>` resté
en clair : c'est ici qu'un trou mal formé (non apparié, imbriqué, avec attribut, sur plusieurs
lignes) est refusé, faute de quoi sa réponse s'afficherait dans le document à trous.

**Comment un trou traverse Pygments.** Pygments lexe le bloc d'un seul tenant : on ne peut pas lui
donner du HTML, ni colorer les morceaux séparément sans perdre l'état du lexeur (chaîne ouverte,
commentaire, accolade). Chaque `<ins>…</ins>` est donc remplacé par une *sentinelle*, un mot fait
de lettres seules (un identifiant pour tout lexeur : jamais découpé, jamais un mot-clé), le bloc
est coloré, puis chaque sentinelle est remplacée dans le HTML produit par le `<span>` du trou ou
de la réponse, qu'elle soit nue ou enveloppée dans un `<span class="…">` du lexeur. Deux garde-fous :

- la sentinelle est choisie absente du bloc (`_prefixe`) : un mot que l'auteur aurait écrit lui-même
  dans son code ne peut pas être pris pour un trou ;
- si, après coloration, une sentinelle ne se retrouve pas **exactement une fois**, ou si le préfixe
  traîne ailleurs, la génération échoue : jamais de document où la réponse manque ou reste visible.
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


def _trous(contenu: str, bloc: str) -> list[re.Match[str]]:
    """Les paires `<ins>…</ins>` d'un bloc ; lève une erreur si une balise `<ins` est mal formée."""
    trous = list(_TROU.finditer(contenu))
    balises = list(_BALISE_INS.finditer(contenu))
    if len(balises) != 2 * len(trous) or any("\n" in t.group(1) for t in trous):
        # toute balise `<ins` qui n'appartient pas à une paire `<ins>…</ins>` sur une seule
        # ligne : non appariée, imbriquée, avec attribut, à cheval sur deux lignes
        propres = {t.start() for t in trous} | {t.end() - len("</ins>") for t in trous}
        fautive = next((m for m in balises if m.start() not in propres), None)
        debut = fautive.start() if fautive else trous[0].start()
        raise ValueError(
            f"balise <ins> mal formée dans un bloc {bloc} (non appariée, avec attribut, "
            f"imbriquée ou sur plusieurs lignes) : …{_fragment(contenu, debut)}…"
        )
    return trous


def _span(reponse: str, mode: Mode) -> str:
    from cielircours.mdtext import Mode  # import tardif : mdtext importe ce module

    if mode is Mode.TROUS:
        return f'<span class="trou" style="--car:{len(reponse.strip())}"></span>'
    return f'<span class="reponse">{escapeHtml(reponse)}</span>'


def _terminal(contenu: str, mode: Mode) -> str:
    """Texte échappé, `<ins>x</ins>` devenu trou ou réponse (bloc sans coloration)."""
    morceaux: list[str] = []
    fin = 0
    for t in _trous(contenu, "terminal"):
        morceaux.append(escapeHtml(contenu[fin : t.start()]))
        morceaux.append(_span(t.group(1), mode))
        fin = t.end()
    morceaux.append(escapeHtml(contenu[fin:]))
    return "".join(morceaux)


def _prefixe(contenu: str) -> str:
    """Début des sentinelles : un mot de lettres seules qui n'apparaît pas dans le bloc.

    Invraisemblable dans un vrai code (il faudrait l'écrire à la main, lettre pour lettre) ; et
    s'il s'y trouvait quand même, on en choisit un autre : il ne peut jamais être confondu avec un trou.
    """
    prefixe = "CielirTrouSentinelle"
    bas = contenu.lower()
    while prefixe.lower() in bas:
        prefixe += "X"
    return prefixe


def _sentinelle(prefixe: str, numero: int) -> str:
    """Sentinelle du trou `numero` : le préfixe, puis quatre lettres (largeur fixe : aucune ne préfixe une autre)."""
    lettres = ""
    for _ in range(4):
        numero, reste = divmod(numero, 26)
        lettres = chr(ord("a") + reste) + lettres
    return prefixe + lettres


def _colorer(contenu: str, lexeur, formateur, langue: str, mode: Mode) -> str:  # type: ignore[no-untyped-def]
    """Coloration Pygments d'un bloc, `<ins>…</ins>` devenus trous par sentinelles."""
    trous = _trous(contenu, "de code")
    if not trous:
        return highlight(contenu, lexeur, formateur)
    prefixe = _prefixe(contenu)
    texte: list[str] = []
    fin = 0
    for n, t in enumerate(trous):
        texte += [contenu[fin : t.start()], _sentinelle(prefixe, n)]
        fin = t.end()
    texte.append(contenu[fin:])
    html = highlight("".join(texte), lexeur, formateur)
    # chaque sentinelle doit être retrouvée une fois, intacte (pas découpée par le lexeur),
    # et le préfixe ne doit rien laisser d'autre : sinon une réponse manquerait ou traînerait
    if html.count(prefixe) != len(trous) or any(html.count(_sentinelle(prefixe, n)) != 1 for n in range(len(trous))):
        raise ValueError(
            f"le lexeur de « {langue} » a découpé ou perdu un trou : impossible de le placer dans "
            f"le bloc coloré (changer l'endroit du trou) : …{_fragment(contenu, trous[0].start())}…"
        )
    for n, t in enumerate(trous):
        html = html.replace(_sentinelle(prefixe, n), _span(t.group(1), mode))
    return html


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
            if not _BALISE_INS.search(jeton.content):
                return defaut(tokens, idx, options, env)
            classe = f' class="language-{escapeHtml(langue)}"' if langue else ""
            return f"<pre><code{classe}>{_terminal(jeton.content, mode)}</code></pre>\n"
        corps = _colorer(jeton.content, lexeur, formateur, langue, mode)
        return f'<pre class="code"><code class="language-{escapeHtml(langue)}">{corps}</code></pre>\n'

    md.renderer.rules["fence"] = fence
