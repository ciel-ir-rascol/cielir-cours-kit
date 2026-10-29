"""Assemblage de markdown-it pour le cours : modes et point d'entrée."""

from enum import StrEnum

from markdown_it import MarkdownIt

from cielircours.plugins.alertes import alertes_plugin
from cielircours.plugins.lignes import lignes_plugin
from cielircours.plugins.trous import trous_plugin


class Mode(StrEnum):
    COMPLET = "complet"
    TROUS = "trous"


def construire_markdown(mode: Mode) -> MarkdownIt:
    md = MarkdownIt("commonmark", {"html": True}).enable("table")
    alertes_plugin(md)
    trous_plugin(md, mode)
    lignes_plugin(md, mode)
    return md


def rendre_corps(source: str, mode: Mode) -> str:
    return construire_markdown(mode).render(source)
