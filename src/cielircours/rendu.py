"""Enveloppe du document : gabarit HTML (cartouche, capacités, licence) puis sortie PDF."""

import datetime
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path

from jinja2 import Environment, StrictUndefined
from weasyprint import HTML
from weasyprint.urls import FatalURLFetchingError, URLFetcher, URLFetcherResponse

from cielircours.config import Cours
from cielircours.mdtext import Mode, rendre_corps
from cielircours.schemas import filtrer_svg, retirer_remplissables

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

    @property
    def release(self) -> str:
        """Ligne de la page de titre du deck : « Release : v1.01 (31.10.26) »."""
        return f"Release : {self.version} ({self.date:%d.%m.%y})"


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
    """Toute ressource introuvable arrête le rendu (WeasyPrint se contenterait d'un avertissement).

    En mode trous, tout SVG reçu (image, fond CSS, `data:`, `<embed>`, image d'un autre SVG)
    est débarrassé de ses étiquettes `.remplissable` avant que WeasyPrint ne le lise.
    """

    def __init__(self, mode: Mode) -> None:
        super().__init__(fail_on_errors=True, allowed_protocols=("file", "data"))
        self._retirer_reponses = mode is Mode.TROUS

    def fetch(self, url, headers=None):  # type: ignore[no-untyped-def]
        reponse = super().fetch(url, headers)
        if not self._retirer_reponses:
            return reponse
        try:
            donnees = reponse.read()
        finally:
            reponse.close()
        return URLFetcherResponse(reponse.url, filtrer_svg(donnees), reponse.headers, reponse.status)


def ouvrir_document(html: str, base_url: Path, mode: Mode) -> HTML:
    """Document WeasyPrint prêt à rendre : ressources contrôlées, réponses des schémas retirées en mode trous."""
    document = HTML(string=html, base_url=str(base_url), url_fetcher=_FetcherStrict(mode))
    if mode is Mode.TROUS:
        retirer_remplissables(document.etree_element)
    return document


def ecrire_pdf(html: str, base_url: Path, sortie: Path, mode: Mode) -> None:
    """Écrit le PDF. `mode` est obligatoire : c'est lui qui retire les réponses des schémas SVG."""
    if not isinstance(mode, Mode):
        raise TypeError(f"mode attendu : un Mode ({', '.join(Mode)}), reçu {mode!r}")
    try:
        rendu = ouvrir_document(html, base_url, mode).render()
    except FatalURLFetchingError as e:
        cause = e.__cause__
        detail = f"{e} ({cause})" if cause else str(e)
        if isinstance(cause, ValueError):
            raise SchemeInterdit(detail) from e
        raise SourceIntrouvable(detail) from e
    rendu.write_pdf(sortie)
