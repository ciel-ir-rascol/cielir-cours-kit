"""Sommaire de la fiche en ligne : une ancre sur chaque titre de partie, et la liste qui y mène.

Seule la fiche à l'écran en reçoit un. Sur le papier, les bandeaux de partie se repèrent d'un
coup d'œil en feuilletant quatre pages, et un sommaire coûterait de la place à une fiche qu'on
veut compacte ; une page web, elle, se parcourt au clic. Le chemin du PDF n'est pas touché.

Le sommaire porte les parties (`##`) et leurs sous-parties (`###`), et s'arrête là : un `####`
n'y figure pas. La numérotation, elle, est faite par la feuille de style avec des compteurs CSS,
des deux côtés — le plan et les titres ne peuvent donc pas diverger.
"""

import re
import unicodedata

_TITRE = re.compile(r"<h(?P<niveau>[23])(?P<attributs>[^>]*)>(?P<contenu>.*?)</h(?P=niveau)>", re.DOTALL)
_BALISE = re.compile(r"<[^>]+>")


def _texte(html: str) -> str:
    return re.sub(r"\s+", " ", _BALISE.sub("", html)).strip()


def _ancre(intitule: str, prises: set[str]) -> str:
    """Une ancre stable, en ASCII : « À vous de jouer : les tableaux » → « a-vous-de-jouer-les-tableaux »."""
    sans_accent = unicodedata.normalize("NFKD", intitule).encode("ascii", "ignore").decode("ascii")
    base = re.sub(r"-{2,}", "-", re.sub(r"[^a-z0-9]+", "-", sans_accent.lower())).strip("-") or "partie"
    ancre, n = base, 2
    while ancre in prises:
        ancre, n = f"{base}-{n}", n + 1
    prises.add(ancre)
    return ancre


Partie = tuple[str, str, list[tuple[str, str]]]


def poser_sommaire(corps: str) -> tuple[str, list[Partie]]:
    """Renvoie `(corps ancré, [(ancre, intitulé, sous-parties), …])`.

    Les titres de niveau 2 sont les parties, ceux de niveau 3 les sous-parties, rattachées à la
    partie qui les précède. Le sommaire s'arrête là : un `####` ne figure pas au plan.

    Lève `ValueError` si une balise `<h2` ou `<h3` du corps n'a pas été reconnue : mieux vaut
    arrêter la génération qu'un sommaire incomplet, qui mènerait vers une ancre inexistante.
    """
    trouves = list(_TITRE.finditer(corps))
    attendus = corps.count("<h2") + corps.count("<h3")
    if len(trouves) != attendus:
        raise ValueError(
            f"sommaire : {attendus} balises <h2 ou <h3 dans le corps mais {len(trouves)} "
            "reconnues (titre mal formé ou à cheval sur plusieurs balises)"
        )
    if any("id=" in m.group("attributs") for m in trouves):
        raise ValueError("sommaire : un titre porte déjà un attribut id")

    prises: set[str] = set()
    parties: list[Partie] = []
    morceaux: list[str] = []
    fin = 0
    for m in trouves:
        niveau, intitule = m.group("niveau"), _texte(m.group("contenu"))
        ancre = _ancre(intitule, prises)
        if niveau == "2" or not parties:
            # un `###` qui précède tout `##` n'a pas de parent : il tient son rang seul
            parties.append((ancre, intitule, []))
        else:
            parties[-1][2].append((ancre, intitule))
        morceaux += [
            corps[fin:m.start()],
            f'<h{niveau} id="{ancre}"{m.group("attributs")}>{m.group("contenu")}</h{niveau}>',
        ]
        fin = m.end()
    morceaux.append(corps[fin:])
    return "".join(morceaux), parties
