"""Ligne de commande : `cielir-cours pdf | deck | site | verifier | td | extraire-sujet`.

Codes de sortie : 0 succès ; 1 infractions trouvées par `verifier` ; 2 erreur (usage,
fichier absent, configuration invalide, ressource introuvable, trou mal formé…).
"""

import argparse
import datetime
import os
import re
import sys
from importlib.resources import files
from pathlib import Path

from cielircours.confidentialite import controler
from cielircours.config import ConfigInvalide, lire_config, lire_td
from cielircours.deck import preparer_deck
from cielircours.depot import nom_du_depot, url_du_depot
from cielircours.mdtext import Mode
from cielircours.rendu import (
    Publication,
    SchemeInterdit,
    SourceIntrouvable,
    ecrire_pdf,
    ecrire_pdf_td,
    rendre_html,
    rendre_html_td,
)
from cielircours.site import ecrire_site
from cielircours.td import Exemplaire, controler_sujet, extraire_sujet

# Un tag de dépôt de cours : v, un numéro de séquence, un point, deux chiffres (v1.02, v12.03).
# Exporté : l'action GitHub du kit le reprend pour refuser un tag malformé avant toute génération.
TAG_VALIDE = re.compile(r"v[0-9]+\.[0-9]{2}\Z")
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
    deck.add_argument("--config", type=Path, help="cours.yml (défaut : celui du dossier qui contient slides/)")
    deck.add_argument("--version", required=True, type=_version, help="par exemple v1.02")
    deck.add_argument("--date", required=True, type=_date, help="AAAA-MM-JJ")
    deck.add_argument("-o", "--sortie", required=True, type=Path)

    site = sous.add_parser("site", help="l'accueil et la fiche de cours à l'écran (HTML)")
    site.add_argument("source", type=Path, help="le COURS.md")
    site.add_argument("--config", type=Path, help="cours.yml (défaut : celui du dossier de COURS.md)")
    site.add_argument("--version", required=True, type=_version, help="par exemple v1.02")
    site.add_argument("--date", required=True, type=_date, help="AAAA-MM-JJ")
    site.add_argument("-o", "--sortie", required=True, type=Path, help="dossier du site (créé au besoin)")

    verifier = sous.add_parser("verifier", help="cherche des informations personnelles dans un dépôt")
    verifier.add_argument("racine", type=Path, nargs="?", default=Path("."))
    verifier.add_argument("--motifs", type=Path, help="fichier de motifs (défaut : celui du kit)")
    td = sous.add_parser("td", help="sujet.pdf (et corrige.pdf dans un -CORR) d'un dépôt de TD")
    td.add_argument("racine", type=Path, help="le dépôt : td.yml et TD.md")
    td.add_argument("--version", required=True, type=_version, help="par exemple v1.02")
    td.add_argument("--date", required=True, type=_date, help="AAAA-MM-JJ")
    td.add_argument("-o", "--sortie", required=True, type=Path, help="dossier des PDF (créé au besoin)")
    td.add_argument("--exemplaire", choices=[e.value for e in Exemplaire],
                    help="forcer le dépôt sujet ou corrigé (sinon : déduit du nom du dépôt, contrôlé)")

    extraire = sous.add_parser("extraire-sujet", help="écrit le dépôt sujet d'un TD depuis son -CORR")
    extraire.add_argument("corr", type=Path, help="le dépôt -CORR")
    extraire.add_argument("sujet", type=Path, help="le dépôt sujet")
    return parser


def _exemplaire_du_depot(racine: Path, nom_attendu_sujet: str, nom_attendu_corr: str) -> Exemplaire:
    nom = nom_du_depot(racine, os.environ)
    if nom is None:
        raise ValueError(
            f"{racine} : nom du dépôt introuvable (ni GITHUB_REPOSITORY, ni remote origin sur "
            "github.com) : passer --exemplaire sujet ou --exemplaire corrige"
        )
    if nom == nom_attendu_corr:
        return Exemplaire.CORRIGE
    if nom == nom_attendu_sujet:
        return Exemplaire.SUJET
    raise ValueError(
        f"le dépôt s'appelle « {nom} », mais td.yml attend « {nom_attendu_sujet} » (sujet) "
        f"ou « {nom_attendu_corr} » (corrigé)"
    )


def _td(args: argparse.Namespace) -> int:
    racine = args.racine.resolve()
    td = lire_td(racine / "td.yml")
    if args.exemplaire:
        depot = Exemplaire(args.exemplaire)
    else:
        depot = _exemplaire_du_depot(racine, td.depot_sujet, td.depot_corr)
    if depot is Exemplaire.SUJET:
        controler_sujet(racine)
    source = (racine / "TD.md").read_text(encoding="utf-8")
    pub = Publication(args.version, args.date)
    args.sortie.mkdir(parents=True, exist_ok=True)
    exemplaires = [Exemplaire.SUJET] if depot is Exemplaire.SUJET else [Exemplaire.SUJET, Exemplaire.CORRIGE]
    for ex in exemplaires:
        sortie = args.sortie / f"{ex.value}.pdf"
        ecrire_pdf_td(rendre_html_td(source, td, pub, ex), racine, sortie, ex)
        print(f"{sortie} ({ex.value}, {args.version})")
    return 0


def _extraire_sujet(args: argparse.Namespace) -> int:
    for rel in extraire_sujet(args.corr, args.sujet):
        print(args.sujet / rel)
    return 0


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
    config = args.config or args.source.resolve().parent.parent / "cours.yml"
    cours = lire_config(config)
    source = args.source.read_bytes().decode("utf-8")
    url = url_du_depot(config.resolve().parent, cours, os.environ)
    copie = preparer_deck(source, Publication(args.version, args.date), cours, url)
    args.sortie.write_bytes(copie.encode("utf-8"))
    print(f"{args.sortie} ({args.version})")
    return 0


def _site(args: argparse.Namespace) -> int:
    config = args.config or args.source.parent / "cours.yml"
    cours = lire_config(config)
    source = args.source.read_text(encoding="utf-8")
    # le lien du dépôt se résout comme pour le deck : on ne le redemande pas
    url = url_du_depot(config.resolve().parent, cours, os.environ)
    ecrire_site(source, args.source.resolve().parent, cours, Publication(args.version, args.date), url, args.sortie)
    print(f"{args.sortie} (site, {args.version})")
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


_COMMANDES = {
    "pdf": _pdf,
    "deck": _deck,
    "site": _site,
    "verifier": _verifier,
    "td": _td,
    "extraire-sujet": _extraire_sujet,
}


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        return _COMMANDES[args.commande](args)
    except _ERREURS as e:
        print(f"erreur : {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
