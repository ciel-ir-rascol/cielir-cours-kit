"""Source d'un TD : contrôles, numérotation et retrait des réponses.

Un TD s'écrit une fois, dans le `TD.md` du dépôt `-CORR`, réponses comprises :

    **Q.** Énoncé…                      question, numérotée Q1, Q2… sur tout le document
    <div class="reponse"> … </div>      sa réponse, juste après ; retirée du sujet
    <div class="ressource" titre="…">   élément de cours, n'importe où
    <div class="dt" titre="…">          document technique, numéroté DT1, DT2…
    <div class="dr" titre="…">          document réponse, numéroté DR1, DR2…, sur sa propre page
    <p class="partie" duree="…" niveau="n"></p>   bandeau d'une partie (niveau de 1 à 4)

Deux exemplaires en sortent : le corrigé (tout) et le sujet (sans aucune réponse, et sans les
éléments `remplissable` des schémas, retirés au rendu comme pour une fiche à trous).

Un TD n'a pas de trous et pas d'écran : `<ins>` et les marques `ecran`/`papier` y sont refusées.
"""

from __future__ import annotations

import html
import os
import re
import shutil
import tempfile
from enum import StrEnum
from pathlib import Path

from cielircours.config import TD, lire_td
from cielircours.schemas import filtrer_svg
from cielircours.supports import (
    _CLASSE_LARGE,
    ATTRIBUT,
    _controler_graphie,
    _fin_stricte,
    _hors_code,
    _lignes_hors_code,
    _motifs_de,
    retirer_blocs,
)
from cielircours.titre import retirer_titre


class Exemplaire(StrEnum):
    SUJET = "sujet"
    CORRIGE = "corrige"


REPONSE = "reponse"
_BLOCS_TITRES = ("ressource", "dt", "dr")

_QUESTION = re.compile(r"^\*\*Q\.\*\*")
# la même grammaire que celle qui retire les réponses : ce qui est apparié est ce qui est retiré
_OUVRANTE_REPONSE = _motifs_de("reponse")[0]
_OUVRANTE_BLOC = re.compile(
    rf'^\s*<div\s+class="(?P<classe>ressource|dt|dr)"(?P<attrs>(?:\s+{ATTRIBUT})*)\s*>\s*$'
)
_PARTIE = re.compile(rf'^\s*<p\s+class="partie"(?P<attrs>(?:\s+{ATTRIBUT})*)\s*>\s*</p>\s*$')
_ATTR = re.compile(r'([a-z][a-z-]*)="([^"]*)"')
_TITRE = re.compile(r"^#{1,6}\s")
_INS = re.compile(r"</?ins\b", re.IGNORECASE)
_CITE_UN_DR = re.compile(r"\bDR\s?[0-9]+\b")


def _refuser_les_interdits(source: str) -> None:
    utile = _hors_code(source)
    m = _INS.search(utile) or _CLASSE_LARGE.search(utile)
    if m is not None:
        extrait = utile[max(0, m.start() - 30):m.end() + 30].replace("\n", " ")
        raise ValueError(
            "trou <ins> ou marque ecran/papier : pas dans un TD. Un TD est un document papier "
            "sans trous ; la réponse s'écrit dans un bloc <div class=\"reponse\"> sous sa "
            f"question. Trouvé : …{extrait}…"
        )


def _apparier(lignes: list[str], exiger_reponses: bool = True) -> None:
    """Chaque question a sa réponse (ou cite un DR), chaque réponse suit une question.

    `exiger_reponses=False` : la source d'un dépôt sujet, d'où les réponses ont été retirées.
    """
    numero = 0
    ouverte: dict | None = None  # {"numero", "texte", "repondue"}

    def fermer() -> None:
        if exiger_reponses and ouverte and not ouverte["repondue"] and not _CITE_UN_DR.search(" ".join(ouverte["texte"])):
            raise ValueError(
                f"la question Q{ouverte['numero']} n'a pas de réponse : un bloc "
                '<div class="reponse"> est attendu juste après elle (sauf si elle porte sur un DR). '
                f"Question : « {' '.join(ouverte['texte'])[:80]} »"
            )

    hors_code = list(_lignes_hors_code(lignes))
    ensemble = set(hors_code)
    sautees: set[int] = set()
    for i in hors_code:
        if i in sautees:
            continue
        ligne = lignes[i]
        if _QUESTION.match(ligne):
            fermer()
            numero += 1
            ouverte = {"numero": numero, "texte": [ligne], "repondue": False}
        elif _OUVRANTE_REPONSE.match(ligne):
            if ouverte is None or ouverte["repondue"]:
                raise ValueError(
                    f"bloc réponse ligne {i + 1} : il ne suit aucune question. Une réponse se "
                    "place juste après le paragraphe **Q.** de sa question, une seule par question."
                )
            ouverte["repondue"] = True
            sautees.update(range(i, _fin_stricte(lignes, i, ensemble, REPONSE) + 1))
        elif _TITRE.match(ligne) or _OUVRANTE_BLOC.match(ligne):
            fermer()
            ouverte = None
        elif ouverte is not None and not ouverte["repondue"]:
            ouverte["texte"].append(ligne)
    fermer()


def _bandeau(attrs: dict[str, str], ligne: int) -> str:
    morceaux = []
    if "duree" in attrs:
        morceaux.append(f'<span class="duree">{html.escape(attrs["duree"])}</span>')
    if "niveau" in attrs:
        niveau = attrs["niveau"]
        if not niveau.isdigit() or not 1 <= int(niveau) <= 4:
            raise ValueError(f"bandeau de partie ligne {ligne} : niveau attendu de 1 à 4, trouvé {niveau!r}")
        n = int(niveau)
        morceaux.append(f'<span class="niveau">{"★" * n}{"☆" * (4 - n)}</span>')
    if not morceaux:
        raise ValueError(f'bandeau de partie ligne {ligne} : attendu duree="…" et/ou niveau="1…4"')
    return f'<p class="partie">{" ".join(morceaux)}</p>'


def _numeroter(lignes: list[str]) -> list[str]:
    sortie = list(lignes)
    compteurs = {"q": 0, "dt": 0, "dr": 0}
    for i in _lignes_hors_code(lignes):
        ligne = lignes[i]
        if _QUESTION.match(ligne):
            compteurs["q"] += 1
            sortie[i] = _QUESTION.sub(f"**Q{compteurs['q']}.**", ligne, count=1)
        elif m := _OUVRANTE_BLOC.match(ligne):
            classe = m.group("classe")
            attrs = dict(_ATTR.findall(m.group("attrs")))
            titre = attrs.get("titre", "").strip()
            if not titre:
                raise ValueError(
                    f'bloc « {classe} » ligne {i + 1} sans titre : attendu <div class="{classe}" titre="…">'
                )
            if classe == "ressource":
                tete = f"Ressource - {html.escape(titre)}"
            else:
                compteurs[classe] += 1
                tete = f"{classe.upper()}{compteurs[classe]} - {html.escape(titre)}"
            sortie[i] = f'<div class="{classe}"><p class="bloc-titre">{tete}</p>'
            if classe == "dr":
                sortie[i] += '<p class="dr-nom">Nom : ……………… — à rendre avec la copie</p>'
        elif m := _PARTIE.match(ligne):
            sortie[i] = _bandeau(dict(_ATTR.findall(m.group("attrs"))), i + 1)
    return sortie


_TRACE_REPONSE = re.compile(r"""class\s*=\s*["']?[^"'>]*\breponse\b""", re.IGNORECASE)


def _refuser_une_trace(source: str, origine: str) -> None:
    if m := _TRACE_REPONSE.search(_hors_code(source)):
        raise ValueError(
            f"{origine} : une trace de réponse subsiste (« {m.group(0)} »). Une réponse s'écrit "
            '<div class="reponse"> seul sur sa ligne, puis une ligne vide, son contenu, et </div> '
            "seul sur sa ligne ; jamais dans une citation ni sur une seule ligne."
        )


def preparer_source(source: str, td: TD, exemplaire: Exemplaire, source_corrigee: bool = True) -> str:
    """La source markdown prête à rendre pour `exemplaire` ; `ValueError` à la moindre incohérence.

    `source_corrigee=False` : la source vient d'un dépôt sujet. Elle ne doit contenir aucune
    réponse, et ses questions n'en attendent pas.
    """
    if not isinstance(exemplaire, Exemplaire):
        raise TypeError(f"exemplaire attendu : un Exemplaire ({', '.join(Exemplaire)}), reçu {exemplaire!r}")
    _refuser_les_interdits(source)
    for classe in (REPONSE, *_BLOCS_TITRES):
        _controler_graphie(source, classe)
    source = retirer_titre(source, td, fichier="TD.md", config="td.yml")
    if not source_corrigee:
        if exemplaire is not Exemplaire.SUJET:
            raise ValueError("un dépôt sujet ne produit que le sujet : il n'a pas les réponses")
        _refuser_une_trace(source, "TD.md du dépôt sujet")
    _apparier(source.split("\n"), exiger_reponses=source_corrigee)
    if exemplaire is Exemplaire.SUJET:
        source = retirer_blocs(source, REPONSE)
        # dernier garde-fou : ce que le filtre n'a pas su retirer ne part pas chez les élèves
        _refuser_une_trace(source, "sujet")
    return "\n".join(_numeroter(source.split("\n")))


# --- Le dépôt sujet -------------------------------------------------------------------------

# La relecture est volontairement plus stricte que le filtre : la moindre trace, même citée dans
# un bloc de code, même en majuscules, arrête tout. Le dépôt sujet est lu par les élèves.
_FUITE = re.compile(r'class\s*=\s*["\']?reponse|remplissable', re.IGNORECASE)


def _fichiers_du_sujet(corr: Path) -> list[Path]:
    """Chemins, relatifs à `corr`, des fichiers que le sujet reçoit : TD.md, td.yml, img/**."""
    fichiers = [Path("TD.md"), Path("td.yml")]
    images = corr / "img"
    if images.is_dir():
        fichiers += sorted(p.relative_to(corr) for p in images.rglob("*") if p.is_file())
    return fichiers


def extraire_sujet(corr: Path, sujet: Path) -> list[Path]:
    """Écrit dans `sujet` le TD sans aucune réponse ; renvoie les chemins écrits, relatifs à `sujet`.

    - `TD.md` : la source du `-CORR` sans ses blocs `reponse` (les `**Q.**` restent à numéroter :
      c'est une source, pas un rendu) ;
    - `td.yml` : copié à l'identique ;
    - `img/**` : les SVG perdent leurs éléments `remplissable`, le reste est copié tel quel.

    Les autres fichiers de `sujet` ne sont ni lus ni modifiés. Tout est écrit d'abord à côté, puis
    relu : une trace de réponse dans un seul fichier, et rien n'est déposé dans `sujet`.
    """
    corr, sujet = Path(corr), Path(sujet)
    source = (corr / "TD.md").read_text(encoding="utf-8")
    preparer_source(source, lire_td(corr / "td.yml"), Exemplaire.CORRIGE)  # le TD doit être sain

    fichiers = _fichiers_du_sujet(corr)
    sujet.mkdir(parents=True, exist_ok=True)
    attente = Path(tempfile.mkdtemp(prefix=".extraire-sujet-", dir=sujet.parent))
    try:
        for rel in fichiers:
            cible = attente / rel
            cible.parent.mkdir(parents=True, exist_ok=True)
            if rel == Path("TD.md"):
                cible.write_text(retirer_blocs(source, REPONSE), encoding="utf-8")
            elif rel.suffix.lower() == ".svg":
                cible.write_bytes(filtrer_svg((corr / rel).read_bytes()))
            else:
                shutil.copyfile(corr / rel, cible)
        for rel in fichiers:
            if rel.suffix.lower() in {".md", ".yml", ".svg"}:
                texte = (attente / rel).read_bytes().decode("utf-8", errors="replace")
                if m := _FUITE.search(texte):
                    raise ValueError(
                        f"{rel.as_posix()} : une trace de réponse subsiste dans le sujet "
                        f"(« {m.group(0)} ») ; rien n'a été écrit dans {sujet}."
                    )
        for rel in fichiers:
            (sujet / rel).parent.mkdir(parents=True, exist_ok=True)
            os.replace(attente / rel, sujet / rel)
    finally:
        shutil.rmtree(attente, ignore_errors=True)
    return fichiers


def controler_sujet(racine: Path) -> None:
    """Refuse un dépôt sujet où subsiste une trace de réponse (TD.md, td.yml ou img/**)."""
    racine = Path(racine)
    for rel in _fichiers_du_sujet(racine):
        if rel.suffix.lower() in {".md", ".yml", ".svg"} and (racine / rel).is_file():
            texte = (racine / rel).read_bytes().decode("utf-8", errors="replace")
            if m := _FUITE.search(texte):
                raise ValueError(
                    f"{rel.as_posix()} : trace de réponse (« {m.group(0)} ») dans un dépôt sujet. "
                    "Les réponses ne vivent que dans le -CORR ; le sujet se régénère par "
                    "`cielir-cours extraire-sujet`."
                )
