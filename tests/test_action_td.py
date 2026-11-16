"""L'action publie un TD comme un cours : même action, type déduit du dépôt."""

from pathlib import Path

import yaml

RACINE = Path(__file__).resolve().parent.parent


def _etapes() -> list[dict]:
    return yaml.safe_load((RACINE / "action.yml").read_text(encoding="utf-8"))["runs"]["steps"]


def test_etape_de_detection_du_type():
    etape = next(e for e in _etapes() if e.get("id") == "type")
    assert "td.yml" in etape["run"] and "cours.yml" in etape["run"]


def test_etapes_du_cours_gardees():
    for e in _etapes():
        run = e.get("run", "")
        if "cielir-cours pdf" in run or "cielir-cours site" in run or "cielir-cours deck" in run:
            assert e.get("if") == "steps.type.outputs.type == 'cours'", e["name"]


def test_etape_du_td():
    etape = next(e for e in _etapes() if "cielir-cours td " in e.get("run", ""))
    assert etape.get("if") == "steps.type.outputs.type == 'td'"


def test_gabarit_publier_td():
    flux = yaml.safe_load((RACINE / "gabarits" / "publier-td.yml").read_text(encoding="utf-8"))
    assert set(flux["jobs"]) == {"construire", "release"}
    texte = (RACINE / "gabarits" / "publier-td.yml").read_text(encoding="utf-8")
    assert "upload-pages-artifact" not in texte and "dist/*.pdf" in texte
