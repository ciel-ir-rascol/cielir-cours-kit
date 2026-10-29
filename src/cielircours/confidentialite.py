"""Contrôle d'information personnelle dans les dépôts de cours (publics).

Porte sur les fichiers du dépôt, jamais sur l'historique git.
"""

import fnmatch
import re
import warnings
from dataclasses import dataclass
from pathlib import Path

import yaml

LONGUEUR_EXTRAIT = 80
DOSSIERS_IGNORES = {".git", ".venv", "node_modules", "__pycache__", "_site", "dist"}


@dataclass(frozen=True)
class Infraction:
    fichier: Path
    ligne: int
    motif: str
    extrait: str


def _charger_motifs(motifs: Path):
    donnees = yaml.safe_load(motifs.read_text(encoding="utf-8")) or {}
    compiles = []
    for nom, definition in donnees.items():
        if nom == "noms":
            for personne in definition or []:
                morceaux = [re.escape(m) for m in str(personne).split()]
                motif = r"(?<!\w)" + r"\s+".join(morceaux) + r"(?!\w)"
                compiles.append(("nom_enseignant", re.compile(motif, re.IGNORECASE), []))
        else:
            exceptions = [re.compile(e + r"\Z") for e in definition.get("exceptions", [])]
            compiles.append((nom, re.compile(definition["expression"]), exceptions))
    return compiles


def _motifs_ignores(racine: Path) -> list[str]:
    fichier = racine / ".cielir-ignore"
    if not fichier.is_file():
        return []
    lignes = (l.strip() for l in fichier.read_text(encoding="utf-8-sig", errors="replace").splitlines())
    return [l.strip("/") for l in lignes if l and not l.startswith("#")]


def _ignore(relatif: Path, ignores: list[str]) -> str | None:
    """Renvoie la raison de l'exclusion (le motif de .cielir-ignore, ou "" pour
    les dossiers ignorés d'office), ou None si le fichier doit être contrôlé."""
    if DOSSIERS_IGNORES.intersection(relatif.parts):
        return ""
    chemin = relatif.as_posix()
    for motif in ignores:
        if chemin == motif or chemin.startswith(motif + "/"):
            return motif
        sans_prefixe = motif.removeprefix("**/")
        if (fnmatch.fnmatch(chemin, motif) or fnmatch.fnmatch(chemin, sans_prefixe)
                or fnmatch.fnmatch(relatif.name, sans_prefixe)):
            return motif
    return None


def _extrait(ligne: str, debut: int, fin: int) -> str:
    """Fenêtre de 80 caractères maximum centrée sur l'occurrence."""
    if len(ligne) > LONGUEUR_EXTRAIT:
        milieu = (debut + fin) // 2
        premier = min(max(0, milieu - LONGUEUR_EXTRAIT // 2), len(ligne) - LONGUEUR_EXTRAIT)
        ligne = ligne[premier:premier + LONGUEUR_EXTRAIT]
    return ligne.strip()


def _lire_texte(fichier: Path) -> str | None:
    donnees = fichier.read_bytes()
    if donnees.startswith((b"\xff\xfe", b"\xfe\xff")):
        return donnees.decode("utf-16", errors="replace")
    if b"\x00" in donnees:
        return None  # binaire
    try:
        return donnees.decode("utf-8")
    except UnicodeDecodeError:
        # Ni UTF-8 ni binaire : texte hérité (cp1252…). On le contrôle quand même.
        return donnees.decode("cp1252", errors="replace")


def controler(racine: Path, motifs: Path) -> list[Infraction]:
    """Renvoie une infraction par occurrence, fichiers et lignes dans l'ordre."""
    compiles = _charger_motifs(motifs)
    ignores = _motifs_ignores(racine)
    infractions = []
    candidats = [p for p in sorted(racine.rglob("*")) if p.is_file() and not p.is_symlink()]
    exclus_par: dict[str, int] = {}
    for fichier in candidats:
        raison = _ignore(fichier.relative_to(racine), ignores)
        if raison is not None:
            if raison:
                exclus_par[raison] = exclus_par.get(raison, 0) + 1
            continue
        texte = _lire_texte(fichier)
        if texte is None:
            continue
        for numero, ligne in enumerate(texte.splitlines(), start=1):
            trouvees = []
            for nom, motif, exceptions in compiles:
                for m in motif.finditer(ligne):
                    if not any(e.match(m.group(0)) for e in exceptions):
                        trouvees.append((m.start(), nom, m.end()))
            for debut, nom, fin in sorted(trouvees):
                infractions.append(Infraction(fichier, numero, nom, _extrait(ligne, debut, fin)))
    if candidats and sum(exclus_par.values()) == len(candidats):
        motifs_en_cause = ", ".join(f"« {m} »" for m in exclus_par)
        warnings.warn(
            f".cielir-ignore exclut tous les fichiers du dépôt ({motifs_en_cause}) : "
            "aucun contrôle n'a eu lieu.",
            stacklevel=2,
        )
    return infractions
