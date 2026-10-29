"""Trous : `<ins>réponse</ins>` devient la réponse (complet) ou un blanc calibré (trous)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from markdown_it import MarkdownIt
from markdown_it.rules_core import StateCore
from markdown_it.token import Token

if TYPE_CHECKING:
    from cielircours.mdtext import Mode


def _html(content: str) -> Token:
    jeton = Token("html_inline", "", 0)
    jeton.content = content
    return jeton


def _texte(jetons: list[Token]) -> str:
    """Texte brut des jetons en ligne, tel que l'étudiant le lirait."""
    return "".join(
        " " if j.type in ("softbreak", "hardbreak") else j.content for j in jetons
    )


def _remplacer(enfants: list[Token], mode: Mode) -> list[Token]:
    resultat: list[Token] = []
    i = 0
    while i < len(enfants):
        jeton = enfants[i]
        if jeton.type == "html_inline" and jeton.content.lower() == "<ins>":
            fin = next(
                (
                    j
                    for j in range(i + 1, len(enfants))
                    if enfants[j].type == "html_inline"
                    and enfants[j].content.lower() == "</ins>"
                ),
                None,
            )
            if fin is not None:
                interieur = enfants[i + 1 : fin]
                if mode == "trous":
                    n = len(_texte(interieur).strip())
                    resultat.append(_html(f'<span class="trou" style="--car:{n}"></span>'))
                else:
                    resultat.append(_html('<span class="reponse">'))
                    resultat.extend(interieur)
                    resultat.append(_html("</span>"))
                i = fin + 1
                continue
        resultat.append(jeton)
        i += 1
    return resultat


def trous_plugin(md: MarkdownIt, mode: Mode) -> None:
    def regle(state: StateCore) -> None:
        for jeton in state.tokens:
            if jeton.type == "inline" and jeton.children:
                jeton.children = _remplacer(jeton.children, mode)

    md.core.ruler.after("inline", "trous_ins", regle)
