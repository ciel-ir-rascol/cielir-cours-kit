"""Schémas SVG à compléter : retrait des étiquettes `.remplissable` dans la version à trous.

Pourquoi retirer au lieu de masquer. WeasyPrint n'applique pas la feuille du document aux
éléments d'un `<svg>` : la règle `body.mode-trous .remplissable { visibility: hidden }` de
`cours.css` masque les étiquettes HTML, pas celles d'un schéma. Et masquer ne suffirait pas :
`visibility` s'hérite mais un enfant peut la rétablir. Une réponse qui fuite est le défaut le
plus grave du kit, donc en mode trous l'élément est supprimé de l'arbre avant le rendu, et son
texte n'existe plus nulle part.

Un SVG entre dans un document par deux chemins, traités tous deux :
- en ligne, dans le HTML : `retirer_remplissables` agit sur l'arbre analysé par WeasyPrint ;
- comme ressource (`<img>`, fond CSS, `data:`, `<embed>`, `<image>` d'un autre SVG) :
  `filtrer_svg` agit sur les octets reçus par le récupérateur d'URL (voir `rendu.py`).
"""

import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element

CLASSE = "remplissable"
ESPACE_SVG = "http://www.w3.org/2000/svg"
_BALISE_SVG = f"{{{ESPACE_SVG}}}svg"

ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")


def _remplissable(element: Element) -> bool:
    return CLASSE in (element.get("class") or "").split()


def _retirer(parent: Element, enfant: Element, precedent: Element | None) -> None:
    """Retire `enfant` de `parent` en gardant le texte qui le suit."""
    queue = enfant.tail or ""
    if precedent is not None:
        precedent.tail = (precedent.tail or "") + queue
    else:
        parent.text = (parent.text or "") + queue
    parent.remove(enfant)


def _purger(parent: Element, dans_svg: bool) -> int:
    retires = 0
    precedent: Element | None = None
    for enfant in list(parent):
        dedans = dans_svg or enfant.tag == _BALISE_SVG or enfant.tag == "svg"
        if dedans and _remplissable(enfant):
            _retirer(parent, enfant, precedent)
            retires += 1
            continue
        retires += _purger(enfant, dedans)
        precedent = enfant
    return retires


def retirer_remplissables(racine: Element) -> int:
    """Retire de l'arbre les éléments `.remplissable` situés dans un `<svg>` ; renvoie leur nombre.

    Un `<svg>` qui porte lui-même la classe est retiré tout entier.
    """
    return _purger(racine, False)


def filtrer_svg(donnees: bytes) -> bytes:
    """Renvoie `donnees` sans les éléments `.remplissable`, si c'est un SVG qui en contient.

    Ce qui n'est pas un SVG (PNG, police, feuille de style, HTML…) et un SVG sans étiquette
    sont renvoyés tels quels, le même objet : le rendu n'en est pas touché. On décide d'après
    le contenu et non d'après le type annoncé ou l'extension, car WeasyPrint essaie le SVG en
    dernier recours pour n'importe quelle image.
    """
    debut = donnees.lstrip(b"\xef\xbb\xbf \t\r\n")
    if not debut.startswith(b"<"):
        return donnees
    try:
        racine = ET.fromstring(donnees)  # l'analyseur même que WeasyPrint : même verdict
    except ET.ParseError:
        return donnees
    if racine.tag != _BALISE_SVG and racine.tag != "svg":
        return donnees
    if _remplissable(racine):
        # un schéma entièrement « à compléter » : il ne reste rien à montrer
        return b'<svg xmlns="%s" width="1" height="1"/>' % ESPACE_SVG.encode()
    if _purger(racine, True) == 0:
        return donnees
    try:
        return ET.tostring(racine, encoding="utf-8", xml_declaration=True, default_namespace=ESPACE_SVG)
    except ValueError:  # éléments sans espace de noms : préfixes générés, tout aussi valides
        return ET.tostring(racine, encoding="utf-8", xml_declaration=True)
