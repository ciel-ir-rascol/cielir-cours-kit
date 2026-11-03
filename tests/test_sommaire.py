"""Le sommaire de la fiche en ligne : ancres sur les titres de partie, et la liste qui y mène."""

import datetime
import re
from pathlib import Path

import pytest

from cielircours.config import lire_config
from cielircours.mdtext import Mode
from cielircours.rendu import Publication, rendre_html
from cielircours.site import rendre_fiche
from cielircours.sommaire import poser_sommaire
from outils import DONNEES

PUB = Publication("v1.02", datetime.date(2026, 11, 3))
URL = "https://github.com/ciel-ir-rascol/cpp-c04-tableauxVecteurs"


def test_chaque_titre_de_partie_recoit_son_ancre():
    corps, parties = poser_sommaire("<h2>Les tableaux statiques</h2><p>x</p><h2>Les vecteurs</h2>")
    assert parties == [("les-tableaux-statiques", "Les tableaux statiques", []),
                       ("les-vecteurs", "Les vecteurs", [])]
    assert '<h2 id="les-tableaux-statiques">Les tableaux statiques</h2>' in corps
    assert '<h2 id="les-vecteurs">Les vecteurs</h2>' in corps


def test_l_ancre_est_en_ascii_malgre_accents_et_ponctuation():
    _, parties = poser_sommaire("<h2>À vous de jouer : les tableaux !</h2>")
    ancre, intitule, _sous = parties[0]
    assert ancre == "a-vous-de-jouer-les-tableaux"
    assert intitule == "À vous de jouer : les tableaux !"  # l'intitulé, lui, garde ses accents


def test_deux_titres_identiques_recoivent_des_ancres_distinctes():
    corps, parties = poser_sommaire("<h2>À vous de jouer</h2><h2>À vous de jouer</h2>")
    assert [a for a, _, _ in parties] == ["a-vous-de-jouer", "a-vous-de-jouer-2"]
    assert corps.count('id="a-vous-de-jouer"') == 1


def test_les_balises_d_un_titre_ne_passent_pas_dans_l_intitule():
    corps, parties = poser_sommaire("<h2>Le mot <code>const</code></h2>")
    assert parties == [("le-mot-const", "Le mot const", [])]
    assert "<code>const</code></h2>" in corps  # le titre affiché garde sa mise en forme


def test_un_titre_que_le_sommaire_ne_reconnait_pas_arrete_la_generation():
    # mieux vaut s'arrêter qu'un sommaire incomplet, qui mènerait vers une ancre inexistante
    with pytest.raises(ValueError, match="sommaire"):
        poser_sommaire("<h2>Bon</h2><h2 class='casse'>")


def test_un_titre_portant_deja_un_id_arrete_la_generation():
    with pytest.raises(ValueError, match="id"):
        poser_sommaire('<h2 id="deja">Partie</h2>')


def test_les_sous_parties_se_rattachent_a_leur_partie():
    corps, parties = poser_sommaire(
        "<h2>Les vecteurs</h2><h3>Définition</h3><h3>Les méthodes</h3><h2>L'essentiel</h2>")
    assert parties == [
        ("les-vecteurs", "Les vecteurs", [("definition", "Définition"),
                                          ("les-methodes", "Les méthodes")]),
        ("l-essentiel", "L'essentiel", []),
    ]
    assert '<h3 id="definition">Définition</h3>' in corps


def test_un_titre_de_niveau_4_ne_figure_pas_au_plan():
    # le sommaire s'arrête aux sous-parties
    corps, parties = poser_sommaire("<h2>Partie</h2><h4>Détail</h4>")
    assert parties == [("partie", "Partie", [])]
    assert "<h4>Détail</h4>" in corps  # laissé tel quel, sans ancre


def test_une_sous_partie_avant_toute_partie_tient_son_rang_seule():
    _, parties = poser_sommaire("<h3>Orpheline</h3><h2>Partie</h2>")
    assert [i for _, i, _ in parties] == ["Orpheline", "Partie"]


def _fiche(source):
    return rendre_fiche(source, lire_config(DONNEES / "cours-cpp.yml"), PUB, URL)


def test_la_fiche_en_ligne_porte_le_sommaire_et_ses_liens_aboutissent():
    html = _fiche("## Les tableaux\n\ntexte\n\n## Les vecteurs\n\ntexte\n")
    bloc = re.search(r'<nav class="sommaire".*?</nav>', html, re.DOTALL)
    assert bloc, "la fiche en ligne n'a pas de sommaire"
    cibles = re.findall(r'href="#([^"]+)"', bloc.group(0))
    ancres = re.findall(r'<h2 id="([^"]+)"', html)
    assert cibles == ancres == ["les-tableaux", "les-vecteurs"]
    assert ">Les tableaux</a>" in bloc.group(0) and ">Les vecteurs</a>" in bloc.group(0)


def test_un_cours_sans_titre_de_partie_n_affiche_pas_de_sommaire_vide():
    assert "sommaire" not in _fiche("Juste un paragraphe.\n")


def test_le_sommaire_ne_touche_pas_au_chemin_du_pdf():
    """Les PDF sont publiés : leur HTML ne doit pas gagner d'ancre au passage."""
    cours = lire_config(DONNEES / "cours-cpp.yml")
    source = "## Les tableaux\n\ntexte\n"
    for mode in (Mode.COMPLET, Mode.TROUS):
        html = rendre_html(source, cours, PUB, mode)
        assert "<h2>Les tableaux</h2>" in html
        assert 'class="sommaire"' not in html
