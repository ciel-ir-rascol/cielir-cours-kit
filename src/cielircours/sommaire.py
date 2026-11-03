"""Sommaire de la fiche en ligne : une ancre sur chaque titre de partie, et la liste qui y mène.

Seule la fiche à l'écran en reçoit un. Sur le papier, les bandeaux de partie se repèrent d'un
coup d'œil en feuilletant quatre pages, et un sommaire coûterait de la place à une fiche qu'on
veut compacte ; une page web, elle, se parcourt au clic. Le chemin du PDF n'est pas touché.

Le sommaire s'arrête aux titres de niveau 2 : il donne le plan du cours, pas sa table complète.
"""

import re
import unicodedata

_H2 = re.compile(r"<h2(?P<attributs>[^>]*)>(?P<contenu>.*?)</h2>", re.DOTALL)
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


def poser_sommaire(corps: str) -> tuple[str, list[tuple[str, str]]]:
    """Renvoie `(corps ancré, [(ancre, intitulé), …])` pour les titres de niveau 2 du corps.

    Lève `ValueError` si une balise `<h2` du corps n'a pas été reconnue : mieux vaut arrêter la
    génération qu'un sommaire incomplet, qui mènerait l'étudiant vers une ancre inexistante.
    """
    trouves = list(_H2.finditer(corps))
    if len(trouves) != corps.count("<h2"):
        raise ValueError(
            f"sommaire : {corps.count('<h2')} balises <h2 dans le corps mais {len(trouves)} "
            "reconnues (titre mal formé ou à cheval sur plusieurs balises)"
        )
    if any(m.group("attributs").find("id=") != -1 for m in trouves):
        raise ValueError("sommaire : un titre de partie porte déjà un attribut id")

    prises: set[str] = set()
    parties: list[tuple[str, str]] = []
    morceaux: list[str] = []
    fin = 0
    for m in trouves:
        intitule = _texte(m.group("contenu"))
        ancre = _ancre(intitule, prises)
        parties.append((ancre, intitule))
        morceaux += [corps[fin:m.start()], f'<h2 id="{ancre}"{m.group("attributs")}>{m.group("contenu")}</h2>']
        fin = m.end()
    morceaux.append(corps[fin:])
    return "".join(morceaux), parties
