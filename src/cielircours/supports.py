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
    i = 0
    while i < len(lignes):
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

    restantes = {m.group(1) for m in _CLASSE.finditer(sortie)}
    if autre in restantes:
        raise ValueError(
            f'une marque class="{autre}" subsiste après filtrage pour le support « {support} » : '
            "elle n'était ni un bloc sur sa propre ligne, ni un <span> sur une seule ligne"
        )
    return sortie
