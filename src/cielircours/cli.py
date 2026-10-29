"""Ligne de commande : `cielir-cours pdf | deck | verifier`.

Codes de sortie : 0 succès ; 1 infractions trouvées par `verifier` ; 2 erreur (usage,
fichier absent, configuration invalide, ressource introuvable, trou mal formé…).
"""

import argparse
import datetime
import re
import sys
from importlib.resources import files
from pathlib import Path

from cielircours.confidentialite import controler
from cielircours.config import ConfigInvalide, lire_config
from cielircours.deck import preparer_deck
from cielircours.mdtext import Mode
from cielircours.rendu import Publication, SchemeInterdit, SourceIntrouvable, ecrire_pdf, rendre_html

# Un tag de dépôt de cours : v, un numéro de séquence, un point, deux chiffres (v1.02, v12.03).
# Exporté : l'action GitHub du kit le reprend pour refuser un tag malformé avant toute génération.
TAG_VALIDE = re.compile(r"v\d+\.\d{2}\Z")
TAG_ATTENDU = "vN.NN, par exemple v1.02"
_ERREURS = (ConfigInvalide, SourceIntrouvable, SchemeInterdit, ValueError, OSError)


def _version(texte: str) -> str:
    if not TAG_VALIDE.match(texte):
        raise argparse.ArgumentTypeError(f"version mal formée : {texte!r} (attendu : {TAG_ATTENDU})")
    return texte


def _date(texte: str) -> datetime.date:
    try:
        return datetime.date.fromisoformat(texte)
    except ValueError:
        raise argparse.ArgumentTypeError(f"date invalide : {texte!r} (attendu : AAAA-MM-JJ)") from None


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cielir-cours", description="Outillage des dépôts de cours CIEL-IR.")
    sous = parser.add_subparsers(dest="commande", required=True)

    pdf = sous.add_parser("pdf", help="COURS.md vers PDF (complet ou à trous)")
    pdf.add_argument("source", type=Path, help="le COURS.md")
    pdf.add_argument("--config", type=Path, help="cours.yml (défaut : celui du dossier de COURS.md)")
    pdf.add_argument("--mode", required=True, choices=[m.value for m in Mode])
    pdf.add_argument("--version", required=True, type=_version, help="par exemple v1.02")
    pdf.add_argument("--date", required=True, type=_date, help="AAAA-MM-JJ")
    pdf.add_argument("-o", "--sortie", required=True, type=Path)

    deck = sous.add_parser("deck", help="copie d'un deck Marp portant la version")
    deck.add_argument("source", type=Path, help="le deck Marp (jamais modifié)")
    deck.add_argument("--version", required=True, type=_version, help="par exemple v1.02")
    deck.add_argument("--date", required=True, type=_date, help="AAAA-MM-JJ")
    deck.add_argument("-o", "--sortie", required=True, type=Path)

    verifier = sous.add_parser("verifier", help="cherche des informations personnelles dans un dépôt")
    verifier.add_argument("racine", type=Path, nargs="?", default=Path("."))
    verifier.add_argument("--motifs", type=Path, help="fichier de motifs (défaut : celui du kit)")
    return parser


def _pdf(args: argparse.Namespace) -> int:
    config = args.config or args.source.parent / "cours.yml"
    cours = lire_config(config)
    mode = Mode(args.mode)
    source = args.source.read_text(encoding="utf-8")
    html = rendre_html(source, cours, Publication(args.version, args.date), mode)
    ecrire_pdf(html, args.source.parent.resolve(), args.sortie, mode)
    print(f"{args.sortie} ({mode.value}, {args.version})")
    return 0


def _deck(args: argparse.Namespace) -> int:
    # lecture en octets : les fins de ligne du deck ne sont pas traduites
    source = args.source.read_bytes().decode("utf-8")
    copie = preparer_deck(source, Publication(args.version, args.date))
    args.sortie.write_bytes(copie.encode("utf-8"))
    print(f"{args.sortie} ({args.version})")
    return 0


def _verifier(args: argparse.Namespace) -> int:
    if not args.racine.is_dir():
        raise FileNotFoundError(f"{args.racine} : dossier introuvable")
    motifs = args.motifs or Path(str(files("cielircours.donnees") / "motifs.yml"))
    infractions = controler(args.racine, motifs)
    for i in infractions:
        print(f"{i.fichier}:{i.ligne}: [{i.motif}] {i.extrait}")
    if infractions:
        print(f"{len(infractions)} infraction(s) : information personnelle à retirer avant publication.")
        return 1
    print(f"{args.racine} : aucune information personnelle trouvée.")
    return 0


_COMMANDES = {"pdf": _pdf, "deck": _deck, "verifier": _verifier}


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        return _COMMANDES[args.commande](args)
    except _ERREURS as e:
        print(f"erreur : {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
