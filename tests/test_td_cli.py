"""Commandes `td` et `extraire-sujet`."""

import shutil
from pathlib import Path

import pytest

from cielircours.cli import main

DONNEES = Path(__file__).parent / "data"
SOURCE = "**Q.** Combien ?\n\n" '<div class="reponse">\n\nTrois.\n\n</div>\n'
CORR, SUJET = "uml-td01-diagClasses-CORR", "uml-td01-diagClasses"


def _depot(tmp_path: Path, source: str = SOURCE) -> Path:
    racine = tmp_path / "depot"
    racine.mkdir()
    shutil.copy(DONNEES / "td.yml", racine / "td.yml")
    (racine / "TD.md").write_text(source, encoding="utf-8")
    return racine


def _td(racine: Path, sortie: Path, *extra: str) -> int:
    return main(["td", str(racine), "--version", "v1.01", "--date", "2026-11-16", "-o", str(sortie), *extra])


def test_corr_produit_les_deux_pdf(tmp_path, monkeypatch):
    monkeypatch.setenv("GITHUB_REPOSITORY", f"ciel-ir-rascol/{CORR}")
    assert _td(_depot(tmp_path), tmp_path / "dist") == 0
    assert sorted(p.name for p in (tmp_path / "dist").iterdir()) == ["corrige.pdf", "sujet.pdf"]


def test_sujet_produit_le_sujet_seul(tmp_path, monkeypatch):
    monkeypatch.setenv("GITHUB_REPOSITORY", f"ciel-ir-rascol/{SUJET}")
    assert _td(_depot(tmp_path, "**Q.** Compléter le DR1.\n"), tmp_path / "dist") == 0
    assert [p.name for p in (tmp_path / "dist").iterdir()] == ["sujet.pdf"]


def test_sujet_refuse_une_reponse(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("GITHUB_REPOSITORY", f"ciel-ir-rascol/{SUJET}")
    assert _td(_depot(tmp_path), tmp_path / "dist") == 2
    assert "réponse" in capsys.readouterr().err


def test_sujet_refuse_un_remplissable(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("GITHUB_REPOSITORY", f"ciel-ir-rascol/{SUJET}")
    racine = _depot(tmp_path, "**Q.** Compléter le DR1.\n")
    (racine / "img").mkdir()
    (racine / "img" / "a.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg">'
                                          '<text class="remplissable">X</text></svg>', encoding="utf-8")
    assert _td(racine, tmp_path / "dist") == 2
    assert "img/a.svg" in capsys.readouterr().err


@pytest.mark.parametrize("nom", ["uml-td01-diagClasses-corr", "uml-td02-diagClasses", "autre"])
def test_nom_inattendu_refuse(tmp_path, monkeypatch, capsys, nom):
    monkeypatch.setenv("GITHUB_REPOSITORY", f"ciel-ir-rascol/{nom}")
    assert _td(_depot(tmp_path), tmp_path / "dist") == 2
    err = capsys.readouterr().err
    assert SUJET in err and CORR in err


def test_nom_introuvable(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv("GITHUB_REPOSITORY", raising=False)
    assert _td(_depot(tmp_path), tmp_path / "dist") == 2
    assert "--exemplaire" in capsys.readouterr().err


def test_exemplaire_force_sans_controle_de_nom(tmp_path, monkeypatch):
    monkeypatch.delenv("GITHUB_REPOSITORY", raising=False)
    assert _td(_depot(tmp_path), tmp_path / "dist", "--exemplaire", "corrige") == 0
    assert (tmp_path / "dist" / "corrige.pdf").is_file()


def test_extraire_sujet_cli(tmp_path, capsys):
    corr = _depot(tmp_path)
    assert main(["extraire-sujet", str(corr), str(tmp_path / "sujet")]) == 0
    out = capsys.readouterr().out
    assert "TD.md" in out and "td.yml" in out
    assert "Trois" not in (tmp_path / "sujet" / "TD.md").read_text(encoding="utf-8")
