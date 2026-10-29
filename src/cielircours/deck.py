"""Injection de la version de publication dans une copie d'un deck Marp.

Marp ne permet pas de surcharger `footer` en ligne de commande : on réécrit
une copie du texte du deck. La source n'est jamais modifiée.
"""

import re

from cielircours.rendu import Publication

_MOIS = (
    "janvier", "février", "mars", "avril", "mai", "juin",
    "juillet", "août", "septembre", "octobre", "novembre", "décembre",
)
_SEPARATEUR = re.compile(r"---[ \t]*")
_FENCE = re.compile(r"\s{0,3}(`{3,}|~{3,})")
_AUTRE_BLOC = re.compile(r"\s{0,3}(#{1,6}(\s|$)|[>|<]|[-*+]\s|\d+[.)]\s|---)")
_PIED = re.compile(r"footer:[ \t]*(.*?)[ \t]*")


def _date_en_lettres(pub: Publication) -> str:
    jour = "1er" if pub.date.day == 1 else str(pub.date.day)
    return f"{jour} {_MOIS[pub.date.month - 1]} {pub.date.year}"


def _valeur_yaml(brut: str) -> str:
    """Valeur d'un scalaire YAML simple, entre guillemets simples, doubles ou nu."""
    if len(brut) >= 2 and brut[0] == brut[-1] == "'":
        return brut[1:-1].replace("''", "'")
    if len(brut) >= 2 and brut[0] == brut[-1] == '"':
        return re.sub(r'\\(["\\])', r"\1", brut[1:-1])
    return brut


def _pied(brut: str | None, libelle: str) -> str:
    existant = _valeur_yaml(brut) if brut is not None else ""
    complet = f"{existant} · {libelle}" if existant else libelle
    return "footer: '" + complet.replace("'", "''") + "'"


def _fin_entete(lignes: list[str]) -> int:
    if not lignes or lignes[0].rstrip() != "---":
        raise ValueError("le deck ne commence pas par un en-tête YAML ouvert par ---")
    for i in range(1, len(lignes)):
        if _SEPARATEUR.fullmatch(lignes[i].rstrip("\r")):
            return i
    raise ValueError("l'en-tête YAML du deck n'est pas refermé par ---")


def _est_paragraphe(ligne: str) -> bool:
    """Ligne de texte courant : un `---` qui la suit la souligne (Setext) au lieu de séparer."""
    return bool(ligne.strip()) and not _AUTRE_BLOC.match(ligne)


def _fin_premiere_slide(lignes: list[str], debut: int) -> int:
    """Indice du premier séparateur de slide, ou len(lignes).

    Ne sont pas des séparateurs : un `---` dans un bloc de code, dans un
    commentaire HTML, ou souligne un paragraphe (titre Setext).
    """
    cloture = None
    en_commentaire = False
    precedente_paragraphe = False
    for i in range(debut, len(lignes)):
        ligne = lignes[i].rstrip("\r")
        if en_commentaire:
            en_commentaire = "-->" not in ligne
            precedente_paragraphe = False
            continue
        fence = _FENCE.match(ligne)
        if cloture is not None:
            if fence and fence.group(1)[0] == cloture[0] and len(fence.group(1)) >= len(cloture):
                cloture = None
            precedente_paragraphe = False
            continue
        if fence:
            cloture = fence.group(1)
            precedente_paragraphe = False
            continue
        if _SEPARATEUR.fullmatch(ligne) and not precedente_paragraphe:
            return i
        if "<!--" in ligne:
            en_commentaire = "-->" not in ligne.split("<!--", 1)[1]
        precedente_paragraphe = _est_paragraphe(ligne)
    return len(lignes)


def preparer_deck(source: str, pub: Publication) -> str:
    """Renvoie une copie du deck dont le pied de page et la première slide portent la version."""
    lignes = source.split("\n")
    fin_entete = _fin_entete(lignes)

    entete = lignes[1:fin_entete]
    for i, ligne in enumerate(entete):
        correspondance = _PIED.fullmatch(ligne.rstrip("\r"))
        if correspondance:
            entete[i] = _pied(correspondance.group(1), pub.libelle)
            break
    else:
        entete.append(_pied(None, pub.libelle))

    fin = _fin_premiere_slide(lignes, fin_entete + 1)
    dernier = fin
    while dernier > fin_entete + 1 and not lignes[dernier - 1].strip():
        dernier -= 1
    mention = f"**{pub.version}** — {_date_en_lettres(pub)}"
    insertion = [mention] if dernier == fin_entete + 1 else ["", mention]

    return "\n".join(
        [lignes[0], *entete, *lignes[fin_entete:dernier], *insertion, *lignes[dernier:]]
    )
