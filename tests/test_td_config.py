"""`td.yml` : métadonnées d'un TD."""

from pathlib import Path

import pytest
import yaml

from cielircours.config import ConfigInvalide, lire_td

DONNEES = Path(__file__).parent / "data"


def _ecrire(tmp_path: Path, **modifs) -> Path:
    brut = yaml.safe_load((DONNEES / "td.yml").read_text(encoding="utf-8"))
    brut.update(modifs)
    chemin = tmp_path / "td.yml"
    chemin.write_text(yaml.safe_dump(brut, allow_unicode=True), encoding="utf-8")
    return chemin


def test_proprietes():
    td = lire_td(DONNEES / "td.yml")
    assert td.titre_page == "TD01 - Diagramme de classes UML"
    assert td.depot_sujet == "uml-td01-diagClasses"
    assert td.depot_corr == "uml-td01-diagClasses-CORR"
    assert td.url_depot == "https://github.com/ciel-ir-rascol/uml-td01-diagClasses"


def test_defauts():
    td = lire_td(DONNEES / "td.yml")
    assert td.autoevaluation is False  # un TD n'est pas évalué : tableau sur demande seulement
    assert td.cours == [] and td.tp == []
    assert td.capacites == ["Lire une classe UML", "Interpréter une multiplicité"]


@pytest.mark.parametrize("numero", [0, 100, "1", True])
def test_numero_invalide(tmp_path, numero):
    with pytest.raises(ConfigInvalide, match="numero"):
        lire_td(_ecrire(tmp_path, numero=numero))


@pytest.mark.parametrize("champ,valeur", [("cours", "uml-c01-x"), ("tp", [1]), ("cours", [None])])
def test_listes_de_depots(tmp_path, champ, valeur):
    with pytest.raises(ConfigInvalide, match=champ):
        lire_td(_ecrire(tmp_path, **{champ: valeur}))


def test_autoevaluation_booleen(tmp_path):
    with pytest.raises(ConfigInvalide, match="autoevaluation"):
        lire_td(_ecrire(tmp_path, autoevaluation="oui"))
    assert lire_td(_ecrire(tmp_path, autoevaluation=True)).autoevaluation is True


def test_champ_absent(tmp_path):
    chemin = _ecrire(tmp_path)
    brut = yaml.safe_load(chemin.read_text(encoding="utf-8"))
    del brut["auteur"]
    chemin.write_text(yaml.safe_dump(brut, allow_unicode=True), encoding="utf-8")
    with pytest.raises(ConfigInvalide, match="auteur"):
        lire_td(chemin)
