"""Alertes GitHub (`> [!NOTE]`, `> [!WARNING]`…) converties en encadrés HTML."""

import re

from markdown_it import MarkdownIt
from markdown_it.rules_core import StateCore
from markdown_it.token import Token

# type GitHub -> (suffixe de classe CSS, titre affiché)
TYPES = {
    "NOTE": ("note", "Note"),
    "TIP": ("astuce", "Astuce"),
    "IMPORTANT": ("important", "Important"),
    "WARNING": ("attention", "Attention"),
    "CAUTION": ("danger", "Danger"),
}

# le marqueur occupe seul la première ligne du premier paragraphe
_MARQUEUR = re.compile(r"\[!(" + "|".join(TYPES) + r")\][ \t]*(?:\n|$)", re.IGNORECASE)


def _html(content: str, level: int) -> Token:
    jeton = Token("html_block", "", 0)
    jeton.content = content
    jeton.block = True
    jeton.level = level
    return jeton


def _retirer_marqueur(jetons: list[Token], i: int, fin_marqueur: int) -> None:
    """Retire le marqueur du paragraphe qui commence à jetons[i] (paragraph_open)."""
    inline = jetons[i + 1]
    inline.content = inline.content[fin_marqueur:]
    enfants = inline.children or []
    for k, enfant in enumerate(enfants):
        if enfant.type in ("softbreak", "hardbreak"):
            inline.children = enfants[k + 1 :]
            break
    else:
        inline.children = []
    if not inline.content:
        del jetons[i : i + 3]  # paragraph_open, inline, paragraph_close


def _regle(state: StateCore) -> None:
    jetons = state.tokens
    i = 0
    while i < len(jetons):
        ouverture = jetons[i]
        if ouverture.type != "blockquote_open":
            i += 1
            continue
        if not (
            i + 2 < len(jetons)
            and jetons[i + 1].type == "paragraph_open"
            and jetons[i + 2].type == "inline"
        ):
            i += 1
            continue
        m = _MARQUEUR.match(jetons[i + 2].content)
        if m is None:
            i += 1
            continue

        classe, titre = TYPES[m.group(1).upper()]
        fermeture = next(
            j
            for j in range(i + 1, len(jetons))
            if jetons[j].type == "blockquote_close" and jetons[j].level == ouverture.level
        )
        jetons[fermeture] = _html("</aside>\n", ouverture.level)
        jetons[i] = _html(
            f'<aside class="alerte alerte--{classe}">\n'
            f'<p class="alerte__titre">{titre}</p>\n',
            ouverture.level,
        )
        _retirer_marqueur(jetons, i + 1, m.end())
        i += 1


def alertes_plugin(md: MarkdownIt) -> None:
    md.core.ruler.after("block", "alertes_github", _regle)
