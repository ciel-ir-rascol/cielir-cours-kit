"""Titre de niveau 1 de COURS.md : retiré avant rendu, refusé s'il contredit cours.yml."""

import shutil
from datetime import date
from pathlib import Path

import pytest
from pypdf import PdfReader

from cielircours.cli import main
from cielircours.config import lire_config
from cielircours.mdtext import Mode
from cielircours.rendu import Publication, rendre_html
from cielircours.titre import retirer_titre

DONNEES = Path(__file__).parent / "data"
COURS = lire_config(DONNEES / "cours-cpp.yml")
TITRE = COURS.titre_page  # « C04 - Tableaux et vecteurs »
PUB = Publication("v1.02", date(2026, 10, 29))
CORPS = "Une phrase d'accroche.\n\n## Partie\n\nUn <ins>mot</ins>.\n"


def test_le_titre_de_niveau_1_est_retire():
    assert retirer_titre(f"# {TITRE}\n\n{CORPS}", COURS) == CORPS


def test_sans_titre_la_source_est_rendue_telle_quelle():
    assert retirer_titre(CORPS, COURS) == CORPS
    assert retirer_titre("", COURS) == ""


def test_les_lignes_vides_d_ouverture_sont_tolerees():
    assert retirer_titre(f"\n\n# {TITRE}\n\n\n{CORPS}", COURS) == CORPS


def test_la_fermeture_atx_et_les_fins_de_ligne_windows_sont_tolerees():
    assert retirer_titre(f"# {TITRE} #\r\n\r\n{CORPS}", COURS) == CORPS


def test_un_titre_de_niveau_2_n_est_pas_touche():
    source = f"## {TITRE}\n\n{CORPS}"
    assert retirer_titre(source, COURS) == source


def test_un_titre_de_niveau_1_plus_loin_n_est_pas_touche():
    source = f"{CORPS}\n# Autre\n"
    assert retirer_titre(source, COURS) == source


def test_un_titre_qui_contredit_cours_yml_est_refuse_avec_l_attendu_et_le_trouve():
    with pytest.raises(ValueError) as e:
        retirer_titre("# C04 - Tableaux\n\n" + CORPS, COURS)
    assert f"attendu « # {TITRE} »" in str(e.value)
    assert "trouvé « # C04 - Tableaux »" in str(e.value)


def test_le_rendu_refuse_un_titre_divergent():
    with pytest.raises(ValueError, match="attendu"):
        rendre_html("# Autre titre\n\n" + CORPS, COURS, PUB, Mode.COMPLET)


def test_le_rendu_est_identique_avec_ou_sans_titre():
    for mode in Mode:
        assert rendre_html(f"# {TITRE}\n\n{CORPS}", COURS, PUB, mode) == rendre_html(CORPS, COURS, PUB, mode)


# ---------- par la ligne de commande ----------

@pytest.fixture
def cours_dir(tmp_path):
    dossier = tmp_path / "cours"
    dossier.mkdir()
    shutil.copy(DONNEES / "cours-cpp.yml", dossier / "cours.yml")
    return dossier


def _pdf(dossier, source, mode="complet"):
    (dossier / "COURS.md").write_text(source, encoding="utf-8")
    sortie = dossier / f"{mode}.pdf"
    code = main(["pdf", str(dossier / "COURS.md"), "--mode", mode, "--version", "v1.02",
                 "--date", "2026-10-29", "-o", str(sortie)])
    return code, sortie


def _texte(chemin):
    return " ".join(" ".join(p.extract_text().split()) for p in PdfReader(chemin).pages)


@pytest.mark.parametrize("mode", ["complet", "trous"])
def test_le_titre_n_apparait_pas_deux_fois_sur_le_pdf(cours_dir, mode):
    code, avec = _pdf(cours_dir, f"# {TITRE}\n\n{CORPS}", mode)
    assert code == 0
    code, sans = _pdf(cours_dir, CORPS, mode)
    assert code == 0
    assert _texte(avec).count(TITRE) == _texte(sans).count(TITRE) == 1


def test_un_cours_sans_titre_de_niveau_1_continue_de_fonctionner(cours_dir):
    code, pdf = _pdf(cours_dir, CORPS)
    assert code == 0 and "Une phrase d'accroche" in _texte(pdf)


def test_la_ligne_de_commande_refuse_un_titre_divergent(cours_dir, capsys):
    code, pdf = _pdf(cours_dir, "# Autre titre\n\n" + CORPS)
    assert code == 2 and not pdf.exists()
    erreur = capsys.readouterr().err
    assert f"attendu « # {TITRE} »" in erreur and "trouvé « # Autre titre »" in erreur
