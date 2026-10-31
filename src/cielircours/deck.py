"""Préparation d'une copie d'un deck Marp pour la publication.

Marp ne permet pas de surcharger `footer` en ligne de commande : on réécrit
une copie du texte du deck. La source n'est jamais modifiée. Ce qui s'y ajoute vient
de `cours.yml` ou de la publication, jamais d'une saisie dans le deck :

- le pied de page et la page de titre portent la version (`Release : v1.01 (31.10.26)`) et
  le lien du dépôt ;
- si `logo` est renseigné, la page de titre porte l'image et le thème l'affiche en haut à droite
  des slides suivantes (variable CSS injectée par la directive `style` de l'en-tête) ;
- garde-fou : le titre, la discipline et la classe de la page de titre, et le pied de page
  (`<discipline> · <séquence> · <classe>`), doivent dire ce que dit `cours.yml`. Un deck et sa configuration qui divergent, c'est la coquille qu'on ne voit jamais :
  la publication s'arrête avec un message explicite.
"""

import re

from cielircours.config import Cours
from cielircours.rendu import Publication

_SEPARATEUR = re.compile(r"---[ \t]*")
_FENCE = re.compile(r"\s{0,3}(`{3,}|~{3,})")
_AUTRE_BLOC = re.compile(r"\s{0,3}(#{1,6}(\s|$)|[>|<]|[-*+]\s|\d+[.)]\s|---)")
_PIED = re.compile(r"footer:[ \t]*(.*?)[ \t]*")
_STYLE = re.compile(r"style[ \t]*:")
# largeur réservée au logo (120 px) et marge avant le titre : voir themes/ciel.css
RESERVE_LOGO = "144px"


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


def _lignes_visibles(lignes: list[str]) -> list[str]:
    """Les lignes d'une slide hors commentaires HTML (directives, notes du présentateur)."""
    visibles, en_commentaire = [], False
    for ligne in lignes:
        ligne = ligne.rstrip("\r")
        if en_commentaire:
            en_commentaire = "-->" not in ligne
            continue
        if ligne.lstrip().startswith("<!--"):
            en_commentaire = "-->" not in ligne
            continue
        visibles.append(ligne)
    return visibles


def _texte(ligne: str) -> str:
    return re.sub(r"^#+\s*", "", ligne.strip()).strip("*_ ")


def _controler_page_de_titre(slide: list[str], cours: Cours) -> None:
    """Refuse un deck dont la page de titre ne dit pas ce que dit `cours.yml`."""
    visibles = [l for l in _lignes_visibles(slide) if l.strip()]
    attendu = [
        ("titre", "# " + cours.titre_page, lambda l: l.startswith("# ") and _texte(l) == cours.titre_page),
        (
            "discipline et séquence",
            f"## {cours.discipline} - {cours.sequence_libelle}",
            lambda l: l.startswith("## ") and _texte(l) == f"{cours.discipline} - {cours.sequence_libelle}",
        ),
        (
            "classe et établissement",
            f"{cours.classe} - {cours.etablissement}",
            lambda l: not l.startswith("#") and _texte(l) == f"{cours.classe} - {cours.etablissement}",
        ),
    ]
    manques = [(nom, ligne) for nom, ligne, ok in attendu if not any(ok(l) for l in visibles)]
    if manques:
        trouve = " | ".join(l.strip() for l in visibles[:4]) or "(rien)"
        details = " ; ".join(f"{nom} : « {ligne} »" for nom, ligne in manques)
        raise ValueError(
            "la page de titre du deck ne correspond pas à cours.yml, publication arrêtée. "
            f"Attendu, absent de la première slide : {details}. Première slide : {trouve}"
        )


def _style_logo(logo: str) -> list[str]:
    return ["style: |", f"  section {{ --logo: url('img/{logo}'); --logo-reserve: {RESERVE_LOGO}; }}"]


def pied_attendu(cours: Cours) -> str:
    """Le pied de page d'un deck, déduit de `cours.yml` : « Informatique · Prog Procédurale · 1CIELIR »."""
    return f"{cours.discipline} · {cours.sequence_libelle} · {cours.classe}"


def _controler_pied(entete: list[str], cours: Cours) -> None:
    attendu = pied_attendu(cours)
    for ligne in entete:
        m = _PIED.fullmatch(ligne.rstrip("\r"))
        if m:
            trouve = _valeur_yaml(m.group(1))
            if trouve != attendu:
                raise ValueError(
                    f"le pied de page du deck ne correspond pas à cours.yml, publication arrêtée. "
                    f"Attendu : footer: '{attendu}'. Trouvé : footer: '{trouve}'"
                )
            return
    raise ValueError(
        "le deck n'a pas de pied de page, publication arrêtée. "
        f"Attendu, dans l'en-tête : footer: '{attendu}' (déduit de cours.yml)"
    )


def preparer_deck(source: str, pub: Publication, cours: Cours, url_depot: str | None = None) -> str:
    """Renvoie une copie du deck : pied, page de titre (logo, release, lien du dépôt) et style du logo.

    `url_depot` : le lien du dépôt réel (voir `depot.py`) ; à défaut, celui déduit du nom.
    Lève `ValueError` si la page de titre ou le pied de page ne correspondent pas à `cours`.
    """
    lignes = source.split("\n")
    fin_entete = _fin_entete(lignes)

    entete = lignes[1:fin_entete]
    _controler_pied(entete, cours)
    for i, ligne in enumerate(entete):
        correspondance = _PIED.fullmatch(ligne.rstrip("\r"))
        if correspondance:
            entete[i] = _pied(correspondance.group(1), pub.libelle)
            break
    else:
        entete.append(_pied(None, pub.libelle))
    if cours.logo:
        if any(_STYLE.match(l) for l in entete):
            raise ValueError("l'en-tête du deck porte déjà une directive `style` : le style du logo vient de cours.yml")
        entete += _style_logo(cours.logo)

    fin = _fin_premiere_slide(lignes, fin_entete + 1)
    slide = lignes[fin_entete + 1 : fin]
    _controler_page_de_titre(slide, cours)

    corps = list(lignes[fin_entete:fin])
    if cours.logo:
        # le logo de la page de titre précède le titre ; `corps[0]` est le séparateur d'en-tête
        for k, ligne in enumerate(corps):
            if k and ligne.startswith("# "):
                corps[k:k] = [f'<img class="logo-titre" src="img/{cours.logo}" alt="Logo">', ""]
                break
    dernier = len(corps)
    while dernier > 1 and not corps[dernier - 1].strip():
        dernier -= 1
    pied = [
        '<div class="pied-titre">',
        "",
        f"{pub.release}\\",
        f"🐙 <{url_depot or cours.url_depot}>",
        "",
        "</div>",
    ]
    insertion = pied if dernier == 1 else ["", *pied]

    return "\n".join([lignes[0], *entete, *corps[:dernier], *insertion, *corps[dernier:], *lignes[fin:]])
