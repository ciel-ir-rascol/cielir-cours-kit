"""Phrase d'amorce : un paragraphe reste avec le tableau, la figure ou le bloc de code qu'il annonce.

Sous WeasyPrint, le CSS seul ne sait pas viser « un paragraphe suivi d'un tableau ». On le marque
donc à la génération : la classe `amorce` est posée sur le paragraphe dont le bloc suivant est un
tableau, une figure, une image seule ou un bloc de code ; `cours.css` y règle `break-after: avoid`.
Sans cela, la consigne (« Retrouvez leurs noms : ») finit une page et son exercice commence la suivante.
"""

import re

from markdown_it import MarkdownIt
from markdown_it.rules_core import StateCore
from markdown_it.token import Token

_IMAGE_SEULE = re.compile(r"!\[[^\]]*\]\([^)\s]+(?:\s+\"[^\"]*\")?\)")
_BLOCS_ANNONCES = {"table_open", "fence", "code_block"}


def _image_seule(jetons: list[Token], i: int) -> bool:
    """Le bloc qui commence en jetons[i] est un paragraphe qui ne contient qu'une image."""
    if i + 2 >= len(jetons) or jetons[i].type != "paragraph_open" or jetons[i + 1].type != "inline":
        return False
    # les enfants ne sont pas encore analysés à ce stade : on lit le texte source
    return _IMAGE_SEULE.fullmatch(jetons[i + 1].content.strip()) is not None


def _figure(jeton: Token) -> bool:
    return jeton.type == "html_block" and jeton.content.lstrip().lower().startswith("<figure")


def _annonce(jetons: list[Token], i: int) -> bool:
    return (
        jetons[i].type in _BLOCS_ANNONCES
        or _figure(jetons[i])
        or _image_seule(jetons, i)
    )


def amorces_plugin(md: MarkdownIt) -> None:
    def regle(state: StateCore) -> None:
        jetons = state.tokens
        for i, jeton in enumerate(jetons):
            if jeton.type != "paragraph_open" or jeton.hidden:
                continue
            suivant = i + 3  # paragraph_open, inline, paragraph_close, puis le bloc suivant
            if suivant < len(jetons) and jetons[i + 2].type == "paragraph_close" and _annonce(jetons, suivant):
                jeton.attrJoin("class", "amorce")

    md.core.ruler.after("block", "amorces", regle)
