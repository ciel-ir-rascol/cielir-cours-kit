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
