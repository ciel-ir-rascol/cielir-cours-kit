"""Assemblage de markdown-it pour le cours : modes et point d'entrée."""

import re
from enum import StrEnum

from markdown_it import MarkdownIt
from markdown_it.renderer import RendererHTML

from cielircours.plugins.alertes import alertes_plugin
from cielircours.plugins.amorces import amorces_plugin
from cielircours.plugins.code import code_plugin
from cielircours.plugins.lignes import lignes_plugin
from cielircours.plugins.trous import trous_plugin


class Mode(StrEnum):
    COMPLET = "complet"
    TROUS = "trous"


_INS_RESTANT = re.compile(r"</?ins\b", re.IGNORECASE)

# Dans un bloc de code, une balise ou une étiquette ÉCHAPPÉE s'imprime en clair, et le contrôle
# ci-dessus ne la voit pas : il cherche la forme brute. Deux accidents réels passaient ainsi —
# un bloc indenté de quatre espaces portant un trou, et un SVG en ligne qu'une ligne blanche
# coupe en bloc de code, étiquette `remplissable` comprise. Le code en ligne (`` `<ins>` ``)
# n'est pas concerné : le README l'annonce littéral, et l'auteur l'a écrit exprès.
_PRE = re.compile(r"<pre\b.*?</pre>", re.DOTALL | re.IGNORECASE)
_ECHAPPE = re.compile(r"&lt;/?ins\b|remplissable", re.IGNORECASE)


class _RenduGarde(RendererHTML):
    """Refuse toute sortie où subsiste une balise `<ins>` : un trou mal formé
    (non apparié, avec attribut, imbriqué…) laisserait sa réponse en clair."""

    def render(self, tokens, options, env):  # type: ignore[no-untyped-def]
        html = super().render(tokens, options, env)
        m = _INS_RESTANT.search(html)
        if m is None:
            for bloc in _PRE.finditer(html):
                echappe = _ECHAPPE.search(bloc.group(0))
                if echappe is not None:
                    m = echappe
                    html = bloc.group(0)
                    break
        if m is not None:
            debut = max(0, m.start() - 30)
            fragment = html[debut : m.start() + 60].replace("\n", " ")
            raise ValueError(
                "une réponse risque de paraître en clair : balise <ins> mal formée (non "
                "appariée, avec attribut, imbriquée, sur plusieurs paragraphes), balise "
                "échappée par un bloc de code, ou étiquette de schéma dans du texte. "
                f"…{fragment}…"
            )
        return html


def construire_markdown(mode: Mode) -> MarkdownIt:
    if not isinstance(mode, Mode):
        raise TypeError(f"mode attendu : un Mode ({', '.join(Mode)}), reçu {mode!r}")
    md = MarkdownIt("commonmark", {"html": True}, renderer_cls=_RenduGarde).enable("table")
    alertes_plugin(md)
    amorces_plugin(md)
    code_plugin(md, mode)
    trous_plugin(md, mode)
    lignes_plugin(md, mode)
    return md


def rendre_corps(source: str, mode: Mode) -> str:
    return construire_markdown(mode).render(source)
