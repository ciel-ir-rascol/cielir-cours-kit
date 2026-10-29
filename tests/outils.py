"""Utilitaires de mesure pour les tests de la feuille de style.

Ils mesurent la mise en page réelle (arbre de boîtes de WeasyPrint) ou analysent le CSS :
chacun a un test qui le met en défaut sur une entrée connue (voir test_cours_css.py).
"""

import re
from datetime import date
from importlib.resources import files
from pathlib import Path

from weasyprint import HTML

from cielircours.config import lire_config
from cielircours.mdtext import Mode
from cielircours.rendu import Publication, _FetcherStrict, rendre_html

DONNEES = Path(__file__).parent / "data"
COURS_CSS = Path(str(files("cielircours.donnees") / "themes" / "cours.css"))

_BLOC = re.compile(r"([^{}]+)\{([^{}]*)\}")


def _sans_commentaires(css: str) -> str:
    return re.sub(r"/\*.*?\*/", "", css, flags=re.DOTALL)


def regle(css: str, selecteur: str) -> str:
    """Corps (concaténé) de toutes les règles dont la liste de sélecteurs contient `selecteur`."""
    corps = []
    for liste, declarations in _BLOC.findall(_sans_commentaires(css)):
        if selecteur in [s.strip() for s in liste.split(",")]:
            corps.append(declarations)
    return "\n".join(corps)


def _luminance_lstar(hexa: str) -> float:
    """Clarté CIE L* d'une couleur sRGB `#rrggbb` (ce que devient la couleur en niveaux de gris)."""
    h = hexa.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    canaux = [int(h[i : i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in canaux]
    y = 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]
    return 116 * (y ** (1 / 3)) - 16 if y > 216 / 24389 else y * 24389 / 27


def contraste(hexa_a: str, hexa_b: str) -> float:
    """Rapport de contraste WCAG entre deux couleurs `#rrggbb`."""

    def y(hexa: str) -> float:
        l_star = _luminance_lstar(hexa)
        return ((l_star + 16) / 116) ** 3 if l_star > 8 else l_star / 903.3

    a, b = sorted((y(hexa_a), y(hexa_b)), reverse=True)
    return (a + 0.05) / (b + 0.05)


def fonds_des_encadres(chemin: Path) -> dict[str, str]:
    """{classe `alerte--x`: couleur de fond `#rrggbb`} lus dans les règles `.alerte--x` du CSS."""
    css = chemin.read_text(encoding="utf-8")
    fonds = {}
    for liste, _ in _BLOC.findall(_sans_commentaires(css)):
        for sel in (s.strip() for s in liste.split(",")):
            m = re.fullmatch(r"\.(alerte--[a-z]+)", sel)
            if m:
                fond = re.search(r"background(?:-color)?\s*:\s*(#[0-9a-fA-F]{3,6})\b", regle(css, sel))
                if fond:
                    fonds[m.group(1)] = fond.group(1)
    return fonds


def luminances_des_fonds(chemin: Path) -> dict[str, float]:
    """{classe `alerte--x`: L* du fond}."""
    return {c: _luminance_lstar(h) for c, h in fonds_des_encadres(chemin).items()}


def pages_rendues(source: str, mode: Mode, tmp_path: Path) -> list:
    """Rend `source` (markdown) avec le gabarit et la feuille réels ; renvoie `document.pages`."""
    cours = lire_config(DONNEES / "cours-cpp.yml")
    html = rendre_html(source, cours, Publication("v1.02", date(2026, 10, 29)), mode)
    return HTML(string=html, base_url=str(tmp_path), url_fetcher=_FetcherStrict()).render().pages


_TYPES_DE_BOITE = {"BlockBox", "InlineBlockBox", "TableBox", "InlineBox"}


def _racine(page):
    return page._page_box.children[0]


def boites(pages: list, classe: str) -> list[tuple[int, object]]:
    """[(numéro de page, boîte)] des boîtes dont l'élément porte la classe `classe`."""
    trouvees = []
    for i, page in enumerate(pages):
        for b in _racine(page).descendants():
            el = getattr(b, "element", None)
            if (
                type(b).__name__ in _TYPES_DE_BOITE
                and el is not None
                and classe in (el.get("class") or "").split()
            ):
                trouvees.append((i, b))
    return trouvees


def debordement_horizontal(pages: list, tolerance: float = 0.5) -> list[tuple[int, str, float]]:
    """Boîtes dont le bord droit dépasse la zone de contenu de la page : [(page, balise, dépassement en px)]."""
    depassements = []
    for i, page in enumerate(pages):
        pb = page._page_box
        limite = pb.content_box_x() + pb.width + tolerance
        for b in _racine(page).descendants():
            if not hasattr(b, "margin_width"):
                continue
            droite = b.position_x + b.margin_width()
            if droite > limite:
                depassements.append((i, b.element_tag, round(droite - limite, 1)))
    return depassements
