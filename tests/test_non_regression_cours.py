"""Le mode TD ne doit rien changer aux cours : le HTML du témoin cours est figé.

L'empreinte a été relevée avant tout changement lié au mode TD. L'URI de la feuille de style,
propre à la machine, est remplacée par FEUILLE avant le calcul.
"""

import hashlib
from datetime import date
from importlib.resources import files
from pathlib import Path

import pytest

from cielircours.config import lire_config
from cielircours.mdtext import Mode
from cielircours.rendu import Publication, rendre_html

RACINE = Path(__file__).resolve().parent.parent
TEMOIN = RACINE / "temoin"
EMPREINTES = Path(__file__).parent / "data" / "temoin-html.sha256"


def empreinte(mode: Mode) -> str:
    cours = lire_config(TEMOIN / "cours.yml")
    source = (TEMOIN / "COURS.md").read_text(encoding="utf-8")
    html = rendre_html(source, cours, Publication("v1.01", date(2026, 10, 29)), mode)
    feuille = Path(str(files("cielircours.donnees") / "themes" / "cours.css")).as_uri()
    return hashlib.sha256(html.replace(feuille, "FEUILLE").encode("utf-8")).hexdigest()


def _attendues() -> dict[str, str]:
    lignes = EMPREINTES.read_text(encoding="utf-8").split("\n")
    return dict(ligne.split() for ligne in lignes if ligne.strip())


@pytest.mark.parametrize("mode", list(Mode))
def test_html_du_temoin_inchange(mode: Mode) -> None:
    assert empreinte(mode) == _attendues()[mode.value]
