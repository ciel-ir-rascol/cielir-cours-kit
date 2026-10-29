"""Assemblage de markdown-it pour le cours : modes et point d'entrée."""

import re
from enum import StrEnum

from markdown_it import MarkdownIt
from markdown_it.renderer import RendererHTML

from cielircours.plugins.alertes import alertes_plugin
from cielircours.plugins.lignes import lignes_plugin
from cielircours.plugins.trous import trous_plugin


class Mode(StrEnum):
    COMPLET = "complet"
    TROUS = "trous"


_INS_RESTANT = re.compile(r"</?ins\b", re.IGNORECASE)


class _RenduGarde(RendererHTML):
    """Refuse toute sortie où subsiste une balise `<ins>` : un trou mal formé
    (non apparié, avec attribut, imbriqué…) laisserait sa réponse en clair."""

    def render(self, tokens, options, env):  # type: ignore[no-untyped-def]
        html = super().render(tokens, options, env)
        m = _INS_RESTANT.search(html)
        if m is not None:
            debut = max(0, m.start() - 30)
            fragment = html[debut : m.start() + 60].replace("\n", " ")
            raise ValueError(
                "balise <ins> mal formée dans le cours (non appariée, avec attribut, "
                f"imbriquée ou sur plusieurs paragraphes) : …{fragment}…"
            )
        return html


def construire_markdown(mode: Mode) -> MarkdownIt:
    if not isinstance(mode, Mode):
        raise TypeError(f"mode attendu : un Mode ({', '.join(Mode)}), reçu {mode!r}")
    md = MarkdownIt("commonmark", {"html": True}, renderer_cls=_RenduGarde).enable("table")
    alertes_plugin(md)
    trous_plugin(md, mode)
    lignes_plugin(md, mode)
    return md


def rendre_corps(source: str, mode: Mode) -> str:
    return construire_markdown(mode).render(source)
