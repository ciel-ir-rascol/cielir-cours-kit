"""Le site du cours : une page d'accueil et la fiche complète à l'écran.

    <sortie>/index.html              l'accueil, seule adresse que les étudiants reçoivent
    <sortie>/fiche/index.html        COURS.md rendu en mode complet (réponses visibles)
    <sortie>/fiche/slides/img/       copie de slides/img/, pour que les chemins relatifs de COURS.md résolvent
    <sortie>/assets/                 site.css, les polices et le logo, servis avec le site (rien ne vient du réseau)

Les slides n'en font pas partie : Marp les écrit à part, sous <sortie>/slides/.

Le corps de la fiche vient du même `rendre_corps` que les PDF (une source, plusieurs rendus) ; seuls
le gabarit et la feuille de style changent. Le chemin du PDF (`rendu.rendre_html`) n'est pas touché.
"""

import shutil
from importlib.resources import files
from pathlib import Path

from cielircours.config import Cours
from cielircours.mdtext import Mode, rendre_corps
from cielircours.rendu import Publication, _environnement
from cielircours.sommaire import poser_sommaire
from cielircours.supports import Support, filtrer
from cielircours.titre import retirer_titre

# polices réellement employées par site.css
_POLICES = (
    "LiberationSans-Regular.woff2", "LiberationSans-Bold.woff2",
    "Inconsolata-Regular.woff2", "Inconsolata-Bold.woff2",
)


def _gabarit(nom: str) -> str:
    return (files("cielircours.donnees") / "gabarits" / nom).read_text(encoding="utf-8")


def rendre_fiche(source: str, cours: Cours, pub: Publication, url_depot: str) -> str:
    """La fiche de cours, mode complet, pour `fiche/index.html`.

    Le corps reçoit une ancre par titre de partie, et le sommaire en tête y mène.
    """
    ecran = filtrer(retirer_titre(source, cours), Support.ECRAN)
    corps, parties = poser_sommaire(rendre_corps(ecran, Mode.COMPLET))
    return _environnement().from_string(_gabarit("fiche.html.j2")).render(
        feuille="../assets/site.css",
        accueil="../",
        diaporama="../slides/",
        cours=cours,
        pub=pub,
        url_depot=url_depot,
        corps=corps,
        sommaire=parties,
    )


def rendre_accueil(cours: Cours, pub: Publication, url_depot: str) -> str:
    """La page d'accueil : trois liens (fiche, diaporama, PDF) et de quoi situer le cours."""
    return _environnement().from_string(_gabarit("accueil.html.j2")).render(
        feuille="assets/site.css",
        cours=cours,
        pub=pub,
        url_depot=url_depot,
        logo=f"assets/logo/{cours.logo}" if cours.logo else None,
    )


def ecrire_site(source: str, racine: Path, cours: Cours, pub: Publication, url_depot: str, sortie: Path) -> None:
    """Écrit le site sous `sortie`. `racine` est le dossier du dépôt de cours (celui de `slides/`)."""
    # tout est calculé avant la première écriture : un cours mal formé ne laisse pas de demi-site
    fiche = rendre_fiche(source, cours, pub, url_depot)
    accueil = rendre_accueil(cours, pub, url_depot)

    (sortie / "fiche").mkdir(parents=True, exist_ok=True)
    (sortie / "index.html").write_text(accueil, encoding="utf-8")
    (sortie / "fiche" / "index.html").write_text(fiche, encoding="utf-8")

    donnees = files("cielircours.donnees") / "themes"
    assets = sortie / "assets"
    (assets / "polices").mkdir(parents=True, exist_ok=True)
    (assets / "site.css").write_bytes((donnees / "site.css").read_bytes())
    for police in _POLICES:
        (assets / "polices" / police).write_bytes((donnees / "polices" / police).read_bytes())

    if cours.logo:  # l'accueil ne dépend pas de la fiche : le logo vit à côté de site.css
        logo = sortie / "assets" / "logo" / cours.logo
        logo.parent.mkdir(parents=True, exist_ok=True)
        logo.write_bytes((racine / "slides" / "img" / cours.logo).read_bytes())

    images = racine / "slides" / "img"
    if images.is_dir():
        copie = sortie / "fiche" / "slides" / "img"
        shutil.rmtree(copie, ignore_errors=True)  # pas d'image périmée d'une génération précédente
        shutil.copytree(images, copie)
