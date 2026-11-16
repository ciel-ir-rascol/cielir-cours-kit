"""Source d'un TD : contrôles, numérotation et retrait des réponses.

Un TD s'écrit une fois, dans le `TD.md` du dépôt `-CORR`, réponses comprises :

    **Q.** Énoncé…                      question, numérotée Q1, Q2… sur tout le document
    <div class="reponse"> … </div>      sa réponse, juste après ; retirée du sujet
    <div class="ressource" titre="…">   élément de cours, n'importe où
    <div class="dt" titre="…">          document technique, numéroté DT1, DT2…
    <div class="dr" titre="…">          document réponse, numéroté DR1, DR2…, sur sa propre page
    <p class="partie" duree="…" niveau="n"></p>   bandeau d'une partie (niveau de 1 à 4)

Deux exemplaires en sortent : le corrigé (tout) et le sujet (sans aucune réponse, et sans les
éléments `remplissable` des schémas, retirés au rendu comme pour une fiche à trous).

Un TD n'a pas de trous et pas d'écran : `<ins>` et les marques `ecran`/`papier` y sont refusées.
"""

from __future__ import annotations

import html
import re
from enum import StrEnum

from cielircours.config import TD
from cielircours.supports import (
    _CLASSE_LARGE,
    _controler_graphie,
    _fin_du_bloc,
    _hors_code,
    _lignes_hors_code,
    retirer_blocs,
)
from cielircours.titre import retirer_titre


class Exemplaire(StrEnum):
    SUJET = "sujet"
    CORRIGE = "corrige"


REPONSE = "reponse"
_BLOCS_TITRES = ("ressource", "dt", "dr")

_QUESTION = re.compile(r"^\*\*Q\.\*\*")
_OUVRANTE_REPONSE = re.compile(r'^\s*<div\s+class="reponse"\s*>\s*$')
_OUVRANTE_BLOC = re.compile(
    r'^\s*<div\s+class="(?P<classe>ressource|dt|dr)"(?P<attrs>(?:\s+[a-z]+="[^"]*")*)\s*>\s*$'
)
_PARTIE = re.compile(r'^\s*<p\s+class="partie"(?P<attrs>(?:\s+[a-z]+="[^"]*")*)\s*>\s*</p>\s*$')
_ATTR = re.compile(r'([a-z]+)="([^"]*)"')
_TITRE = re.compile(r"^#{1,6}\s")
_INS = re.compile(r"</?ins\b", re.IGNORECASE)
_CITE_UN_DR = re.compile(r"\bDR\s?[0-9]+\b")


def _refuser_les_interdits(source: str) -> None:
    utile = _hors_code(source)
    m = _INS.search(utile) or _CLASSE_LARGE.search(utile)
    if m is not None:
        extrait = utile[max(0, m.start() - 30):m.end() + 30].replace("\n", " ")
        raise ValueError(
            "trou <ins> ou marque ecran/papier : pas dans un TD. Un TD est un document papier "
            "sans trous ; la réponse s'écrit dans un bloc <div class=\"reponse\"> sous sa "
            f"question. Trouvé : …{extrait}…"
        )


def _apparier(lignes: list[str]) -> None:
    """Chaque question a sa réponse (ou cite un DR), chaque réponse suit une question."""
    numero = 0
    ouverte: dict | None = None  # {"numero", "texte", "repondue"}

    def fermer() -> None:
        if ouverte and not ouverte["repondue"] and not _CITE_UN_DR.search(" ".join(ouverte["texte"])):
            raise ValueError(
                f"la question Q{ouverte['numero']} n'a pas de réponse : un bloc "
                '<div class="reponse"> est attendu juste après elle (sauf si elle porte sur un DR). '
                f"Question : « {' '.join(ouverte['texte'])[:80]} »"
            )

    sautees: set[int] = set()
    for i in _lignes_hors_code(lignes):
        if i in sautees:
            continue
        ligne = lignes[i]
        if _QUESTION.match(ligne):
            fermer()
            numero += 1
            ouverte = {"numero": numero, "texte": [ligne], "repondue": False}
        elif _OUVRANTE_REPONSE.match(ligne):
            if ouverte is None or ouverte["repondue"]:
                raise ValueError(
                    f"bloc réponse ligne {i + 1} : il ne suit aucune question. Une réponse se "
                    "place juste après le paragraphe **Q.** de sa question, une seule par question."
                )
            ouverte["repondue"] = True
            sautees.update(range(i, _fin_du_bloc(lignes, i) + 1))
        elif _TITRE.match(ligne) or _OUVRANTE_BLOC.match(ligne):
            fermer()
            ouverte = None
        elif ouverte is not None and not ouverte["repondue"]:
            ouverte["texte"].append(ligne)
    fermer()


def _bandeau(attrs: dict[str, str], ligne: int) -> str:
    morceaux = []
    if "duree" in attrs:
        morceaux.append(f'<span class="duree">{html.escape(attrs["duree"])}</span>')
    if "niveau" in attrs:
        niveau = attrs["niveau"]
        if not niveau.isdigit() or not 1 <= int(niveau) <= 4:
            raise ValueError(f"bandeau de partie ligne {ligne} : niveau attendu de 1 à 4, trouvé {niveau!r}")
        n = int(niveau)
        morceaux.append(f'<span class="niveau">{"★" * n}{"☆" * (4 - n)}</span>')
    if not morceaux:
        raise ValueError(f'bandeau de partie ligne {ligne} : attendu duree="…" et/ou niveau="1…4"')
    return f'<p class="partie">{" ".join(morceaux)}</p>'


def _numeroter(lignes: list[str]) -> list[str]:
    sortie = list(lignes)
    compteurs = {"q": 0, "dt": 0, "dr": 0}
    for i in _lignes_hors_code(lignes):
        ligne = lignes[i]
        if _QUESTION.match(ligne):
            compteurs["q"] += 1
            sortie[i] = _QUESTION.sub(f"**Q{compteurs['q']}.**", ligne, count=1)
        elif m := _OUVRANTE_BLOC.match(ligne):
            classe = m.group("classe")
            attrs = dict(_ATTR.findall(m.group("attrs")))
            titre = attrs.get("titre", "").strip()
            if not titre:
                raise ValueError(
                    f'bloc « {classe} » ligne {i + 1} sans titre : attendu <div class="{classe}" titre="…">'
                )
            if classe == "ressource":
                tete = f"Ressource - {html.escape(titre)}"
            else:
                compteurs[classe] += 1
                tete = f"{classe.upper()}{compteurs[classe]} - {html.escape(titre)}"
            sortie[i] = f'<div class="{classe}"><p class="bloc-titre">{tete}</p>'
            if classe == "dr":
                sortie[i] += '<p class="dr-nom">Nom : ……………… — à rendre avec la copie</p>'
        elif m := _PARTIE.match(ligne):
            sortie[i] = _bandeau(dict(_ATTR.findall(m.group("attrs"))), i + 1)
    return sortie


def preparer_source(source: str, td: TD, exemplaire: Exemplaire) -> str:
    """La source markdown prête à rendre pour `exemplaire` ; `ValueError` à la moindre incohérence."""
    if not isinstance(exemplaire, Exemplaire):
        raise TypeError(f"exemplaire attendu : un Exemplaire ({', '.join(Exemplaire)}), reçu {exemplaire!r}")
    _refuser_les_interdits(source)
    for classe in (REPONSE, *_BLOCS_TITRES):
        _controler_graphie(source, classe)
    source = retirer_titre(source, td, fichier="TD.md", config="td.yml")
    _apparier(source.split("\n"))
    if exemplaire is Exemplaire.SUJET:
        source = retirer_blocs(source, REPONSE)
    return "\n".join(_numeroter(source.split("\n")))
