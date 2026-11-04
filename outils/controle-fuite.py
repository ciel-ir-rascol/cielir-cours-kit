"""Aucune réponse ne doit être lisible dans la fiche à trous publiée.

Depuis la racine du kit :

    uv run --with pymupdf python outils/controle-fuite.py <dépôt> <cours-a-trous.pdf>

Le script importe le kit — il rend le document exactement comme la publication le rend — donc
il tourne dans l'environnement du kit. `--with pymupdf` ajoute la seule dépendance qui n'en
fait pas partie : elle ne sert qu'aux contrôles, jamais à la génération.

À lancer sur le PDF **téléchargé depuis la release**, pas sur une génération locale : c'est le
document que les étudiants reçoivent qu'on contrôle, pas celui qu'on espère avoir produit.

Le texte de référence n'est pas `COURS.md` privé de ses réponses, mais le HTML que le kit rend
lui-même en mode trous — donc exactement ce qui doit paraître. Trois sources de faux positifs
s'y ajoutent, découvertes à répétition et chacune payée :

1. les **étiquettes des SVG** sont des `<img>` dans le HTML et du texte dans le PDF ;
   `filtrer_svg` leur applique le même retrait qu'au rendu, donc on obtient ce qui reste lisible ;
2. l'**en-tête courant** est écrit une fois dans le HTML et répété à chaque page ;
3. **Pygments découpe un littéral en jetons** que l'extraction du PDF recolle — d'où la
   comparaison sur des textes privés de tout espace.

Un écart signalé n'est pas forcément une fuite : une matrice qu'un exercice fait lire, une
déclaration rappelée au-dessus d'une question sont des redites voulues. L'outil dit où
regarder ; il ne remplace pas la lecture de la fiche.
"""

from __future__ import annotations

import argparse
import datetime
import re
import sys
from pathlib import Path

import pymupdf

from cielircours.config import lire_config
from cielircours.mdtext import Mode
from cielircours.rendu import Publication, rendre_html
from cielircours.schemas import filtrer_svg
from cielircours.supports import Support, filtrer

_BALISE = re.compile(r"<[^>]+>")
_SCRIPT = re.compile(r"<(script|style)\b.*?</\1>", re.DOTALL)
_INS = re.compile(r"<ins(?:\s+lignes=\"\d+\")?>(.*?)</ins>", re.DOTALL)


def _sans_balise(html: str) -> str:
    return _BALISE.sub(" ", _SCRIPT.sub(" ", html))


def _compact(texte: str) -> str:
    return re.sub(r"\s+", "", texte)


def controler(depot: Path, pdf: Path, version: str) -> int:
    source = (depot / "COURS.md").read_text(encoding="utf-8")
    cours = lire_config(depot / "cours.yml")
    pub = Publication(version, datetime.date.today())
    papier = filtrer(source, Support.PAPIER)

    attendu = _sans_balise(rendre_html(source, cours, pub, Mode.TROUS))
    for rel in sorted(set(re.findall(r'src="([^"]+\.svg)"', papier)
                          + re.findall(r"\]\(([^)]+\.svg)\)", papier))):
        chemin = depot / rel
        if chemin.is_file():
            attendu += " " + _sans_balise(filtrer_svg(chemin.read_bytes()).decode("utf-8"))

    pages = [p.get_text() for p in pymupdf.open(pdf)]
    courant = (f"{cours.sequence} {cours.titre} {cours.discipline} – {cours.classe} "
               f"{cours.etablissement} · {cours.auteur}")
    attendu += (" " + courant) * (len(pages) - 1)

    visible, imprime = _compact(attendu), _compact(" ".join(pages))
    reponses = {_compact(_sans_balise(m.group(1))) for m in _INS.finditer(papier)}
    longues = sorted(r for r in reponses if len(r) >= 5)
    ecarts = [(r, imprime.count(r), visible.count(r)) for r in longues
              if imprime.count(r) > visible.count(r)]

    print(f"{depot.name} : {len(pages)} pages, {len(reponses)} réponses distinctes, "
          f"{len(longues)} de 5 caractères et plus")
    print(f"  écarts : {len(ecarts)}")
    for reponse, dans_pdf, attendues in ecarts:
        print(f"    « {reponse[:70]} »  pdf={dans_pdf} attendu={attendues}")
    if ecarts:
        print("\n  Un écart n'est pas toujours une fuite : vérifier si la redite est voulue.")
    return 1 if ecarts else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("depot", type=Path, help="le dépôt de cours (celui de cours.yml)")
    parser.add_argument("pdf", type=Path, help="cours-a-trous.pdf, téléchargé depuis la release")
    parser.add_argument("--version", default="v0.00", help="sans effet sur le contrôle")
    args = parser.parse_args()
    return controler(args.depot, args.pdf, args.version)


if __name__ == "__main__":
    sys.exit(main())
