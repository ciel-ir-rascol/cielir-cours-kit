"""Trous : `<ins>réponse</ins>` devient la réponse (complet) ou un blanc calibré (trous)."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from markdown_it import MarkdownIt
from markdown_it.rules_core import StateCore
from markdown_it.token import Token

if TYPE_CHECKING:
    from cielircours.mdtext import Mode


_INS = re.compile(r"</?ins\b", re.IGNORECASE)


def _fragment(valeur: str) -> str:
    m = _INS.search(valeur)
    debut = max(0, m.start() - 30) if m else 0
    return valeur[debut : debut + 90].replace("\n", " ")


def _controler_jeton(jeton: Token) -> None:
    """Refuse un `<ins>` dans la valeur d'un attribut ou l'info d'un bloc de code.

    Ces valeurs sortent échappées (`&lt;ins&gt;`) : le contrôle après rendu ne les voit
    pas, et la réponse apparaîtrait en clair. Le texte d'un code span ou d'un bloc de
    code n'est pas concerné et reste littéral.
    """
    for nom, valeur in jeton.attrs.items():
        if isinstance(valeur, str) and _INS.search(valeur):
            raise ValueError(
                f"balise <ins> dans l'attribut {nom!r} (titre de lien ou d'image) : "
                f"…{_fragment(valeur)}…"
            )
    if jeton.type == "fence" and _INS.search(jeton.info):
        raise ValueError(
            f"balise <ins> dans l'info d'un bloc de code : …{_fragment(jeton.info)}…"
        )
    if jeton.type == "image":
        # dans le texte alternatif, les balises sont retirées au rendu mais leur contenu reste :
        # une balise `<ins` que `trous_ins` n'a pas consommée (non appariée, forme à attribut)
        # ferait sortir sa réponse en clair, sans que le garde-fou après rendu ne la voie
        for enfant in jeton.children or []:
            if enfant.type == "html_inline" and _INS.match(enfant.content):
                raise ValueError(f"balise <ins> mal formée dans un texte alternatif d'image : …{_fragment(enfant.content)}…")
    for enfant in jeton.children or []:
        _controler_jeton(enfant)


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
    from cielircours.mdtext import Mode  # import tardif : mdtext importe ce module

    resultat: list[Token] = []
    i = 0
    while i < len(enfants):
        jeton = enfants[i]
        if jeton.type == "image" and jeton.children:
            # le texte alternatif est rendu depuis les enfants de l'image
            jeton.children = _remplacer(jeton.children, mode)
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
                if mode is Mode.TROUS:
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
    from cielircours.mdtext import Mode

    if not isinstance(mode, Mode):
        raise TypeError(f"mode attendu : un Mode, reçu {mode!r}")

    def regle(state: StateCore) -> None:
        for jeton in state.tokens:
            if jeton.type == "inline" and jeton.children:
                jeton.children = _remplacer(jeton.children, mode)

    def controle(state: StateCore) -> None:
        for jeton in state.tokens:
            _controler_jeton(jeton)

    md.core.ruler.after("inline", "trous_ins", regle)
    md.core.ruler.after("trous_ins", "trous_attributs", controle)
