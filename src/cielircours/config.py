"""Lecture et validation du fichier de métadonnées `cours.yml`."""

import re
from dataclasses import dataclass
from pathlib import Path

import yaml

_SEQUENCE = re.compile(r"[a-z0-9]+")
_SLUG = re.compile(r"[a-z][A-Za-z0-9]*")
_CHAMPS_TEXTE = ("titre", "discipline", "classe", "etablissement", "duree")


class ConfigInvalide(ValueError):
    """Le `cours.yml` est illisible, incomplet ou ne respecte pas les conventions."""


@dataclass(frozen=True)
class Cours:
    sequence: str
    bloc: int
    slug: str
    titre: str
    discipline: str
    classe: str
    etablissement: str
    duree: str
    tp: str | None
    capacites: list[str]

    @property
    def depot(self) -> str:
        return f"{self.sequence}-c{self.bloc:02d}-{self.slug}"


def lire_config(chemin: Path) -> Cours:
    try:
        brut = yaml.safe_load(Path(chemin).read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as e:
        raise ConfigInvalide(f"{chemin} : lecture impossible ({e})") from e
    if not isinstance(brut, dict):
        raise ConfigInvalide(f"{chemin} : un dictionnaire YAML est attendu")

    manquants = [c for c in ("sequence", "bloc", "slug", *_CHAMPS_TEXTE) if c not in brut]
    if manquants:
        raise ConfigInvalide(f"{chemin} : champs obligatoires absents : {', '.join(manquants)}")

    sequence, bloc, slug = brut["sequence"], brut["bloc"], brut["slug"]
    if not isinstance(sequence, str) or not _SEQUENCE.fullmatch(sequence):
        raise ConfigInvalide(f"{chemin} : sequence invalide : {sequence!r}")
    if not isinstance(bloc, int) or isinstance(bloc, bool) or not 1 <= bloc <= 99:
        raise ConfigInvalide(f"{chemin} : bloc doit être un entier entre 1 et 99 : {bloc!r}")
    if not isinstance(slug, str) or not _SLUG.fullmatch(slug):
        raise ConfigInvalide(f"{chemin} : slug invalide : {slug!r}")
    for champ in _CHAMPS_TEXTE:
        if not isinstance(brut[champ], str) or not brut[champ].strip():
            raise ConfigInvalide(f"{chemin} : {champ} doit être un texte non vide")

    tp = brut.get("tp")
    if tp is not None and not isinstance(tp, str):
        raise ConfigInvalide(f"{chemin} : tp doit être un texte")
    capacites = brut.get("capacites") or []
    if not isinstance(capacites, list) or not all(isinstance(c, str) for c in capacites):
        raise ConfigInvalide(f"{chemin} : capacites doit être une liste de textes")

    return Cours(
        sequence=sequence,
        bloc=bloc,
        slug=slug,
        titre=brut["titre"],
        discipline=brut["discipline"],
        classe=brut["classe"],
        etablissement=brut["etablissement"],
        duree=brut["duree"],
        tp=tp,
        capacites=capacites,
    )
