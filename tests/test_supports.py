"""Passages réservés à un support : `<div class="ecran">` et `<div class="papier">`."""

import datetime

import pytest

from cielircours.config import lire_config
from cielircours.mdtext import Mode
from cielircours.rendu import Publication, rendre_html
from cielircours.site import rendre_fiche
from cielircours.supports import Support, filtrer
from outils import DONNEES

PUB = Publication("v1.02", datetime.date(2026, 11, 3))
URL = "https://github.com/ciel-ir-rascol/cpp-c04-tableauxVecteurs"

SOURCE = (
    "Partout.\n\n"
    '<div class="ecran">\n\n'
    "Seulement en ligne.\n\n"
    "</div>\n\n"
    '<div class="papier">\n\n'
    "*Écrivez à la main :*\n\n"
    "</div>\n\n"
    "Partout aussi.\n"
)


def test_une_source_sans_marque_ne_change_pas_d_un_iota():
    # les cours déjà écrits et publiés doivent rendre exactement comme avant
    source = "## Partie\n\nUn <ins>trou</ins>.\n\n```cpp\nint t[5];\n```\n"
    for support in Support:
        assert filtrer(source, support) == source


def test_le_papier_garde_sa_marque_et_perd_celle_de_l_ecran():
    sortie = filtrer(SOURCE, Support.PAPIER)
    assert "Seulement en ligne." not in sortie
    assert "*Écrivez à la main :*" in sortie
    assert "Partout." in sortie and "Partout aussi." in sortie


def test_l_ecran_garde_sa_marque_et_perd_celle_du_papier():
    sortie = filtrer(SOURCE, Support.ECRAN)
    assert "Seulement en ligne." in sortie
    assert "Écrivez à la main" not in sortie
    assert "Partout." in sortie and "Partout aussi." in sortie


def test_un_bloc_retire_ne_laisse_pas_de_trou_de_lignes_blanches():
    sortie = filtrer(SOURCE, Support.PAPIER)
    assert "\n\n\n" not in sortie


def test_un_div_imbrique_n_interrompt_pas_le_bloc():
    source = ('<div class="ecran">\n\n<div class="cols">\n\ndeux colonnes\n\n</div>\n\n</div>\n\n'
              "Après.\n")
    assert "deux colonnes" not in filtrer(source, Support.PAPIER)
    assert "Après." in filtrer(source, Support.PAPIER)
    assert "deux colonnes" in filtrer(source, Support.ECRAN)


def test_un_span_reserve_disparait_de_l_autre_support():
    source = 'Une phrase <span class="ecran">avec une incise</span> et la suite.\n'
    assert "avec une incise" not in filtrer(source, Support.PAPIER)
    assert "et la suite." in filtrer(source, Support.PAPIER)
    assert "avec une incise" in filtrer(source, Support.ECRAN)


def test_une_marque_non_refermee_arrete_la_generation():
    # sinon un bloc entier disparaîtrait d'un document sans que rien ne le signale
    with pytest.raises(ValueError, match="non refermée"):
        filtrer('<div class="ecran">\n\nsans fin\n', Support.PAPIER)


def test_une_marque_que_le_filtre_ne_sait_pas_lire_arrete_la_generation():
    # ici la marque n'est pas seule sur sa ligne : elle ne serait ni retirée ni rendue
    with pytest.raises(ValueError, match="subsiste"):
        filtrer('texte <div class="papier">collé</div> au milieu\n', Support.ECRAN)


def test_le_passage_reserve_a_l_ecran_est_absent_des_deux_pdf():
    cours = lire_config(DONNEES / "cours-cpp.yml")
    for mode in (Mode.COMPLET, Mode.TROUS):
        html = rendre_html(SOURCE, cours, PUB, mode)
        assert "Seulement en ligne" not in html
        assert "Écrivez à la main" in html


def test_le_passage_reserve_au_papier_est_absent_de_la_fiche_en_ligne():
    cours = lire_config(DONNEES / "cours-cpp.yml")
    html = rendre_fiche(SOURCE, cours, PUB, URL)
    assert "Seulement en ligne" in html
    assert "Écrivez à la main" not in html
