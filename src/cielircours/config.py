"""Lecture et validation du fichier de métadonnées `cours.yml`."""

import re
from dataclasses import dataclass
from pathlib import Path

import yaml

_SEQUENCE = re.compile(r"[a-z0-9]+")
_SLUG = re.compile(r"[a-z][A-Za-z0-9]*")
_CHAMPS_TEXTE = ("sequence_libelle", "auteur", "titre", "discipline", "classe", "etablissement", "duree")
# un chemin sous slides/img/ : lettres, chiffres, point, tiret, souligné, barre ; jamais « .. »
_LOGO = re.compile(r"[A-Za-z0-9_-][A-Za-z0-9._/-]*\.(?:svg|png|jpe?g|webp)")
ORGANISATION = "ciel-ir-rascol"


class ConfigInvalide(ValueError):
    """Le `cours.yml` est illisible, incomplet ou ne respecte pas les conventions."""


@dataclass(frozen=True)
class Cours:
    sequence: str
    sequence_libelle: str
    auteur: str
    bloc: int
    slug: str
    titre: str
    discipline: str
    classe: str
    etablissement: str
    duree: str
    tp: str | None
    capacites: list[str]
    logo: str | None = None

    @property
    def titre_page(self) -> str:
        """Titre affiché en tête de la page de titre du deck et du cartouche de la fiche : « C04 - Titre »."""
        return f"C{self.bloc:02d} - {self.titre}"

    @property
    def url_depot(self) -> str:
        return f"https://github.com/{ORGANISATION}/{self.depot}"

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

    logo = brut.get("logo") or None  # « logo: » vide : pas de logo
    if logo is not None:
        if not isinstance(logo, str) or not _LOGO.fullmatch(logo) or ".." in logo:
            raise ConfigInvalide(
                f"{chemin} : logo doit être un chemin sous slides/img/ vers une image "
                f"(svg, png, jpg, webp), sans « .. » : {logo!r}"
            )
        if not (Path(chemin).parent / "slides" / "img" / logo).is_file():
            raise ConfigInvalide(f"{chemin} : logo introuvable : slides/img/{logo}")

    return Cours(
        sequence=sequence,
        sequence_libelle=brut["sequence_libelle"],
        auteur=brut["auteur"],
        bloc=bloc,
        slug=slug,
        titre=brut["titre"],
        discipline=brut["discipline"],
        classe=brut["classe"],
        etablissement=brut["etablissement"],
        duree=brut["duree"],
        tp=tp,
        capacites=capacites,
        logo=logo,
    )


# --- TD : `td.yml` --------------------------------------------------------------------------


@dataclass(frozen=True)
class TD:
    """Métadonnées d'un TD, lues dans `td.yml` (le même fichier dans le sujet et le `-CORR`)."""

    sequence: str
    sequence_libelle: str
    auteur: str
    numero: int
    slug: str
    titre: str
    discipline: str
    classe: str
    etablissement: str
    duree: str
    cours: list[str]
    tp: list[str]
    capacites: list[str]
    autoevaluation: bool = False  # un TD n'est pas évalué : le tableau ne vient que sur demande

    @property
    def titre_page(self) -> str:
        """Titre du cartouche : « TD01 - Titre »."""
        return f"TD{self.numero:02d} - {self.titre}"

    @property
    def depot_sujet(self) -> str:
        return f"{self.sequence}-td{self.numero:02d}-{self.slug}"

    @property
    def depot_corr(self) -> str:
        return f"{self.depot_sujet}-CORR"

    @property
    def url_depot(self) -> str:
        return f"https://github.com/{ORGANISATION}/{self.depot_sujet}"


def _liste_de_textes(chemin: Path, brut: dict, champ: str) -> list[str]:
    valeur = brut.get(champ) or []
    if not isinstance(valeur, list) or not all(isinstance(v, str) and v.strip() for v in valeur):
        raise ConfigInvalide(f"{chemin} : {champ} doit être une liste de textes : {valeur!r}")
    return valeur


def lire_td(chemin: Path) -> TD:
    try:
        brut = yaml.safe_load(Path(chemin).read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as e:
        raise ConfigInvalide(f"{chemin} : lecture impossible ({e})") from e
    if not isinstance(brut, dict):
        raise ConfigInvalide(f"{chemin} : un dictionnaire YAML est attendu")

    manquants = [c for c in ("sequence", "numero", "slug", *_CHAMPS_TEXTE) if c not in brut]
    if manquants:
        raise ConfigInvalide(f"{chemin} : champs obligatoires absents : {', '.join(manquants)}")

    sequence, numero, slug = brut["sequence"], brut["numero"], brut["slug"]
    if not isinstance(sequence, str) or not _SEQUENCE.fullmatch(sequence):
        raise ConfigInvalide(f"{chemin} : sequence invalide : {sequence!r}")
    if not isinstance(numero, int) or isinstance(numero, bool) or not 1 <= numero <= 99:
        raise ConfigInvalide(f"{chemin} : numero doit être un entier entre 1 et 99 : {numero!r}")
    if not isinstance(slug, str) or not _SLUG.fullmatch(slug):
        raise ConfigInvalide(f"{chemin} : slug invalide : {slug!r}")
    for champ in _CHAMPS_TEXTE:
        if not isinstance(brut[champ], str) or not brut[champ].strip():
            raise ConfigInvalide(f"{chemin} : {champ} doit être un texte non vide")

    autoevaluation = brut.get("autoevaluation", False)
    if not isinstance(autoevaluation, bool):
        raise ConfigInvalide(f"{chemin} : autoevaluation doit valoir true ou false : {autoevaluation!r}")

    return TD(
        sequence=sequence,
        sequence_libelle=brut["sequence_libelle"],
        auteur=brut["auteur"],
        numero=numero,
        slug=slug,
        titre=brut["titre"],
        discipline=brut["discipline"],
        classe=brut["classe"],
        etablissement=brut["etablissement"],
        duree=brut["duree"],
        cours=_liste_de_textes(chemin, brut, "cours"),
        tp=_liste_de_textes(chemin, brut, "tp"),
        capacites=_liste_de_textes(chemin, brut, "capacites"),
        autoevaluation=autoevaluation,
    )
