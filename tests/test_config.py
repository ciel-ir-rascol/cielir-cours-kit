from pathlib import Path

import pytest

from cielircours.config import ConfigInvalide, lire_config


def test_depot_compose_le_nom_normalise():
    c = lire_config(Path("tests/data/cours-cpp.yml"))
    assert c.depot == "cpp-c04-tableauxVecteurs"


def test_bloc_est_sur_deux_chiffres():
    assert lire_config(Path("tests/data/cours-bloc1.yml")).depot.startswith("git-c01-")


@pytest.mark.parametrize("fichier", ["slug-majuscule.yml", "bloc-zero.yml", "sans-titre.yml"])
def test_config_invalide_leve(fichier):
    with pytest.raises(ConfigInvalide):
        lire_config(Path("tests/data") / fichier)


def _yml(tmp_path, retrait=(), ajout=""):
    texte = (Path("tests/data") / "cours-cpp.yml").read_text(encoding="utf-8")
    lignes = [l for l in texte.splitlines() if not any(l.startswith(r + ":") for r in retrait)]
    (tmp_path / "cours.yml").write_text("\n".join(lignes) + "\n" + ajout, encoding="utf-8")
    return tmp_path / "cours.yml"


def test_sequence_libelle_est_obligatoire(tmp_path):
    with pytest.raises(ConfigInvalide, match="sequence_libelle"):
        lire_config(_yml(tmp_path, retrait=("sequence_libelle",)))


def test_titre_de_page_et_url_se_deduisent(tmp_path):
    c = lire_config(_yml(tmp_path))
    assert c.titre_page == "C04 - Tableaux et vecteurs" and c.sequence_libelle == "Prog Procédurale"
    assert c.url_depot == "https://github.com/ciel-ir-rascol/cpp-c04-tableauxVecteurs"


def test_le_logo_est_facultatif(tmp_path):
    assert lire_config(_yml(tmp_path)).logo is None


def test_un_logo_existant_est_lu(tmp_path):
    (tmp_path / "slides" / "img").mkdir(parents=True)
    (tmp_path / "slides" / "img" / "logo.svg").write_text("<svg/>")
    assert lire_config(_yml(tmp_path, ajout="logo: logo.svg\n")).logo == "logo.svg"


@pytest.mark.parametrize("logo", ["../x.svg", "/etc/x.svg", "a b.svg", "x.exe", "x", "'x.svg\\ny'", "a/../b.svg"])
def test_un_logo_invalide_leve(tmp_path, logo):
    with pytest.raises(ConfigInvalide, match="logo"):
        lire_config(_yml(tmp_path, ajout=f"logo: {logo}\n"))


def test_un_logo_absent_du_dossier_leve(tmp_path):
    with pytest.raises(ConfigInvalide, match="introuvable"):
        lire_config(_yml(tmp_path, ajout="logo: absent.svg\n"))


@pytest.mark.parametrize("ajout", ["logo:\n", "logo: ''\n", "logo: null\n"])
def test_un_logo_vide_est_pas_de_logo(tmp_path, ajout):
    assert lire_config(_yml(tmp_path, ajout=ajout)).logo is None
