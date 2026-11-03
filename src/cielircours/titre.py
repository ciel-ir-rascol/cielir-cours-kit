"""Titre de niveau 1 de `COURS.md` : toléré en tête, retiré avant rendu, jamais divergent.

Un `COURS.md` peut s'ouvrir sur `# C04 - Titre`, pour qu'un lecteur qui tombe sur le fichier
sache de quoi il parle. Le cartouche des PDF et l'en-tête de la fiche en ligne portent déjà ce
titre : le kit retire donc la ligne avant rendu, sans quoi il s'afficherait deux fois.

Garde-fou : ce titre recopie `cours.yml` (`Cours.titre_page`). S'il le contredit, la génération
s'arrête, avec l'attendu et le trouvé — comme pour le deck. Un `COURS.md` sans titre de niveau 1
(les dépôts antérieurs) passe tel quel, au caractère près.
"""

import re

from cielircours.config import Cours

# Titre ATX de niveau 1 : jusqu'à 3 espaces, « # », le texte, des « # » de fermeture facultatifs.
_TITRE = re.compile(r"[ ]{0,3}#[ \t]+(?P<texte>.*?)(?:[ \t]+#+)?[ \t]*\r?")


def retirer_titre(source: str, cours: Cours) -> str:
    """`source` sans son titre de niveau 1 d'ouverture ; `ValueError` s'il contredit `cours.yml`."""
    lignes = source.splitlines(keepends=True)
    i = 0
    while i < len(lignes) and not lignes[i].strip():
        i += 1
    if i == len(lignes):
        return source
    m = _TITRE.fullmatch(lignes[i].rstrip("\n"))
    if m is None:
        return source
    trouve = m.group("texte")
    if trouve != cours.titre_page:
        raise ValueError(
            "le titre de niveau 1 de COURS.md ne dit pas ce que dit cours.yml "
            f"(titre_page) : attendu « # {cours.titre_page} », trouvé « # {trouve} »"
        )
    i += 1
    while i < len(lignes) and not lignes[i].strip():
        i += 1
    return "".join(lignes[i:])
