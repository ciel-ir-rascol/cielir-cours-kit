"""Passages réservés à un support : `<div class="ecran">` et `<div class="papier">`.

Un cours s'écrit une fois mais sort sur deux supports qui n'ont pas les mêmes contraintes. La
fiche imprimée est compacte et porte des consignes de geste (« écrivez à la main… ») qui n'ont
aucun sens à l'écran ; la page web, elle, peut dérouler un développement que quatre pages ne
tiendraient pas. D'où une marque par support, et une seule source.

    <div class="ecran">      ne paraît que sur la fiche en ligne
    <div class="papier">     ne paraît que sur les deux PDF
    (non marqué)             paraît partout — c'est le cas courant

Il existe aussi `<span class="ecran">…</span>` pour une incise au milieu d'une phrase.

**On retire, on ne masque pas.** Le kit a appris la leçon avec les étiquettes des schémas
(`schemas.py`) : masquer en CSS laisse le texte dans le document, et un enfant peut rétablir la
visibilité. Le passage de l'autre support est donc retiré de la source avant tout rendu.

Le `<div>` a été préféré à une syntaxe `:::` parce qu'il **se dégrade bien** : sur GitHub, dans
VS Code, dans n'importe quel rendu markdown, le contenu s'affiche et la marque est invisible,
là où un `:::` s'afficherait en toutes lettres.
"""

from __future__ import annotations

import re
from enum import StrEnum


class Support(StrEnum):
    ECRAN = "ecran"
    PAPIER = "papier"


_OUVRANTE = re.compile(r'^\s*<div\s+class="(?P<support>ecran|papier)"\s*>\s*$')
_DIV = re.compile(r"<\s*(?P<fermante>/?)div\b", re.IGNORECASE)
_SPAN = re.compile(r'<span\s+class="(?P<support>ecran|papier)"\s*>(?P<contenu>.*?)</span>')
_CLASSE = re.compile(r'class="(ecran|papier)"')
# large à dessein : toute graphie d'une marque, pour attraper celles que le filtre NE SAIT PAS
# lire — guillemets simples, majuscules, espaces autour du `=`, classe accompagnée d'une autre.
# Elles passaient sans erreur, et le passage finissait sur les deux supports.
_CLASSE_LARGE = re.compile(r"""class\s*=\s*["']?[^"'>]*\b(ecran|papier)\b""", re.IGNORECASE)
_FENCE = re.compile(r"^\s{0,3}(?P<cloture>`{3,}|~{3,})")


def _fin_du_bloc(lignes: list[str], debut: int) -> int:
    """Indice de la ligne `</div>` qui ferme le bloc ouvert en `debut`, en comptant les imbriqués."""
    profondeur = 0
    for i in range(debut, len(lignes)):
        for m in _DIV.finditer(lignes[i]):
            profondeur += -1 if m.group("fermante") else 1
            if profondeur == 0:
                return i
    raise ValueError(
        f"marque de support non refermée, ouverte ligne {debut + 1} : « {lignes[debut].strip()} ». "
        "Chaque <div class=\"ecran\"> ou <div class=\"papier\"> attend son </div>."
    )


def filtrer(source: str, support: Support) -> str:
    """Renvoie `source` privée des passages réservés à l'autre support.

    Une source sans marque est renvoyée telle quelle, caractère pour caractère : les cours déjà
    écrits ne changent pas d'un iota, et le rendu des PDF publiés reste identique.
    """
    autre = Support.PAPIER if support is Support.ECRAN else Support.ECRAN

    lignes = source.split("\n")
    gardees: list[str] = []
    cloture: str | None = None  # le délimiteur du bloc de code ouvert, s'il y en a un
    i = 0
    while i < len(lignes):
        # un bloc de code n'est pas du texte : une marque qu'il contient est documentée, pas
        # posée, et un `</div>` qu'il cite ne ferme rien
        fence = _FENCE.match(lignes[i])
        if cloture is not None:
            if fence and lignes[i].strip().startswith(cloture):
                cloture = None
            gardees.append(lignes[i])
            i += 1
            continue
        if fence:
            cloture = fence.group("cloture")
            gardees.append(lignes[i])
            i += 1
            continue

        ouvrante = _OUVRANTE.match(lignes[i])
        if ouvrante:
            fin = _fin_du_bloc(lignes, i)
            if ouvrante.group("support") == autre:
                # le bloc entier disparaît, ligne blanche comprise, pour ne pas laisser de trou
                i = fin + 1
                while i < len(lignes) and not lignes[i].strip() and gardees and not gardees[-1].strip():
                    i += 1
                continue
            gardees += lignes[i:fin + 1]
            i = fin + 1
            continue
        gardees.append(lignes[i])
        i += 1

    sortie = "\n".join(gardees)
    sortie = _SPAN.sub(lambda m: "" if m.group("support") == autre else m.group(0), sortie)

    _controler(sortie, support, autre)
    return sortie


def _hors_code(texte: str) -> str:
    """`texte` privé de ses blocs de code : ce qu'ils citent n'est pas une marque posée."""
    gardees, cloture = [], None
    for ligne in texte.split("\n"):
        fence = _FENCE.match(ligne)
        if cloture is not None:
            if fence and ligne.strip().startswith(cloture):
                cloture = None
            continue
        if fence:
            cloture = fence.group("cloture")
            continue
        gardees.append(ligne)
    return "\n".join(gardees)


def _controler(sortie: str, support: Support, autre: Support) -> None:
    """Refuse ce qui subsiste de l'autre support, et toute marque écrite d'une façon illisible.

    Le second cas est le plus traître : `<div class='ecran'>` ne déclenchait rien et le passage
    paraissait sur les deux supports. On compare donc les graphies exactes, les seules que le
    filtre sache lire, au total des graphies possibles.
    """
    utile = _hors_code(sortie)
    if autre in {m.group(1) for m in _CLASSE.finditer(utile)}:
        raise ValueError(
            f'une marque class="{autre}" subsiste après filtrage pour le support « {support} » : '
            "elle n'était ni un bloc sur sa propre ligne, ni un <span> sur une seule ligne"
        )
    exactes = len(_CLASSE.findall(utile))
    toutes = len(_CLASSE_LARGE.findall(utile))
    if toutes > exactes:
        fautive = next(m for m in _CLASSE_LARGE.finditer(utile)
                       if not _CLASSE.match(utile, m.start()))
        extrait = utile[max(0, fautive.start() - 30):fautive.end() + 30].replace("\n", " ")
        raise ValueError(
            "marque de support écrite d'une façon que le filtre ne sait pas lire : attendu "
            '`<div class="ecran">` ou `<div class="papier">`, seuls sur leur ligne, en '
            f"minuscules et entre guillemets doubles. Trouvé : …{extrait}…"
        )
