"""Le lien du dépôt vient du dépôt réel : GITHUB_REPOSITORY, puis le remote git, puis le nom déduit."""

import subprocess
from pathlib import Path

import pytest

from cielircours.config import lire_config
from cielircours.depot import url_du_depot

COURS = lire_config(Path(__file__).parent / "data" / "cours-cpp.yml")
DEDUIT = "https://github.com/ciel-ir-rascol/cpp-c04-tableauxVecteurs"


def _depot_git(chemin, remote):
    subprocess.run(["git", "init", "-q", str(chemin)], check=True)
    if remote:
        subprocess.run(["git", "-C", str(chemin), "remote", "add", "origin", remote], check=True)
    return chemin


def test_github_repository_fait_autorite(tmp_path):
    racine = _depot_git(tmp_path, "git@github.com:autre/autre-depot.git")
    assert url_du_depot(racine, COURS, {"GITHUB_REPOSITORY": "ciel-ir-rascol/cielir-cours-temoin"}) \
        == "https://github.com/ciel-ir-rascol/cielir-cours-temoin"


@pytest.mark.parametrize("remote", [
    "git@github.com:ciel-ir-rascol/cielir-cours-temoin.git",
    "https://github.com/ciel-ir-rascol/cielir-cours-temoin.git",
    "https://github.com/ciel-ir-rascol/cielir-cours-temoin",
    "ssh://git@github.com/ciel-ir-rascol/cielir-cours-temoin.git",
    "https://jeton-secret@github.com/ciel-ir-rascol/cielir-cours-temoin.git",
    "https://utilisateur:motdepasse@github.com/ciel-ir-rascol/cielir-cours-temoin.git",
])
def test_le_remote_sert_a_defaut_et_ses_identifiants_ne_sont_jamais_repris(tmp_path, remote):
    url = url_du_depot(_depot_git(tmp_path, remote), COURS, {})
    assert url == "https://github.com/ciel-ir-rascol/cielir-cours-temoin"
    assert "secret" not in url and "motdepasse" not in url


@pytest.mark.parametrize("env", [{}, {"GITHUB_REPOSITORY": ""}, {"GITHUB_REPOSITORY": "pas un depot"}, {"GITHUB_REPOSITORY": "a/b/c"}])
def test_sans_rien_d_autre_le_nom_deduit_sert_de_dernier_recours(tmp_path, env):
    assert url_du_depot(_depot_git(tmp_path, None), COURS, env) == DEDUIT


@pytest.mark.parametrize("remote", ["https://gitlab.com/x/y.git", "/chemin/local/depot", "git@exemple.org:x/y.git"])
def test_un_remote_hors_github_est_ignore(tmp_path, remote):
    assert url_du_depot(_depot_git(tmp_path, remote), COURS, {}) == DEDUIT


def test_hors_d_un_depot_git_le_nom_deduit_sert(tmp_path):
    assert url_du_depot(tmp_path, COURS, {}) == DEDUIT
