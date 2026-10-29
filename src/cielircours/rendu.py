"""Enveloppe du document : gabarit HTML (cartouche, capacités, licence) puis sortie PDF."""

import datetime
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path

from jinja2 import Environment, StrictUndefined
from weasyprint import HTML
from weasyprint.urls import FatalURLFetchingError, URLFetcher

from cielircours.config import Cours
from cielircours.mdtext import Mode, rendre_corps

LICENCE = "CC BY-NC-SA 4.0"

_TYPES_DOCUMENT = {Mode.COMPLET: "Cours", Mode.TROUS: "Cours à trous"}


class SourceIntrouvable(FileNotFoundError):
    """Une ressource locale du document (image, feuille de style…) est introuvable."""


class SchemeInterdit(ValueError):
    """Le document référence une ressource hors `file:`/`data:` (réseau : génération non reproductible)."""


@dataclass(frozen=True)
class Publication:
    version: str
    date: datetime.date

    @property
    def libelle(self) -> str:
        return f"{self.version} du {self.date:%d.%m.%y}"


def _environnement() -> Environment:
    return Environment(autoescape=True, undefined=StrictUndefined, trim_blocks=True, lstrip_blocks=True)


def rendre_html(source: str, cours: Cours, pub: Publication, mode: Mode) -> str:
    gabarit = (files("cielircours.donnees") / "gabarits" / "cours.html.j2").read_text(encoding="utf-8")
    feuille = Path(str(files("cielircours.donnees") / "themes" / "cours.css")).as_uri()
    return _environnement().from_string(gabarit).render(
        feuille=feuille,
        cours=cours,
        pub=pub,
        mode=mode,
        type_document=_TYPES_DOCUMENT[mode],
        licence=LICENCE,
        corps=rendre_corps(source, mode),
    )


class _FetcherStrict(URLFetcher):
    """Toute ressource introuvable arrête le rendu (WeasyPrint se contenterait d'un avertissement)."""

    def __init__(self) -> None:
        super().__init__(fail_on_errors=True, allowed_protocols=("file", "data"))


def ecrire_pdf(html: str, base_url: Path, sortie: Path) -> None:
    document = HTML(string=html, base_url=str(base_url), url_fetcher=_FetcherStrict())
    try:
        rendu = document.render()
    except FatalURLFetchingError as e:
        cause = e.__cause__
        detail = f"{e} ({cause})" if cause else str(e)
        if isinstance(cause, ValueError):
            raise SchemeInterdit(detail) from e
        raise SourceIntrouvable(detail) from e
    rendu.write_pdf(sortie)
