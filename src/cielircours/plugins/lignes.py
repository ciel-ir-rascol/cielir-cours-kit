"""Réponses rédigées : `:::reponse n` devient la réponse (complet) ou n lignes à écrire (trous)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from markdown_it import MarkdownIt
from markdown_it.rules_core import StateCore
from markdown_it.token import Token
from mdit_py_plugins.container import container_plugin

if TYPE_CHECKING:
    from cielircours.mdtext import Mode

NOM = "reponse"


def _html(content: str, level: int) -> Token:
    jeton = Token("html_block", "", 0)
    jeton.content = content
    jeton.block = True
    jeton.level = level
    return jeton


def _nombre_de_lignes(info: str) -> int:
    texte = info.strip().removeprefix(NOM).strip()
    if not texte.isdigit() or int(texte) < 1:
        # échec franc : un bloc mal formé retomberait en paragraphe et fuiterait la réponse
        raise ValueError(f"`:::{NOM}` attend un nombre de lignes entier positif, reçu {texte!r}")
    return int(texte)


def lignes_plugin(md: MarkdownIt, mode: Mode) -> None:
    # tout paramètre est accepté ici ; la validité est contrôlée dans la règle
    container_plugin(md, NOM, validate=lambda params, markup: True)

    def regle(state: StateCore) -> None:
        jetons = state.tokens
        i = 0
        while i < len(jetons):
            ouverture = jetons[i]
            if ouverture.type != f"container_{NOM}_open":
                i += 1
                continue
            n = _nombre_de_lignes(ouverture.info)
            fermeture = next(
                j
                for j in range(i + 1, len(jetons))
                if jetons[j].type == f"container_{NOM}_close"
                and jetons[j].level == ouverture.level
            )
            if mode == "trous":
                jetons[i : fermeture + 1] = [
                    _html(f'<div class="lignes" style="--n:{n}"></div>\n', ouverture.level)
                ]
            else:
                jetons[fermeture] = _html("</div>\n", ouverture.level)
                jetons[i] = _html('<div class="reponse-bloc">\n', ouverture.level)
            i += 1

    md.core.ruler.after("block", "lignes_reponse", regle)
