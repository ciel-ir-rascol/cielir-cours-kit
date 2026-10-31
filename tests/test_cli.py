import shutil
from pathlib import Path

import pytest
from pypdf import PdfReader

from cielircours.cli import main

DONNEES = Path(__file__).parent / "data"
SOURCE = "# Partie\n\nUn <ins>SECRET</ins> ici.\n"


@pytest.fixture
def cours_dir(tmp_path):
    dossier = tmp_path / "cours"
    dossier.mkdir()
    shutil.copy(DONNEES / "cours-cpp.yml", dossier / "cours.yml")
    (dossier / "COURS.md").write_text(SOURCE, encoding="utf-8")
    return dossier


def _pdf(dossier, *extra, mode="complet", sortie="x.pdf"):
    return main(
        ["pdf", str(dossier / "COURS.md"), "--mode", mode, "--version", "v1.02",
         "--date", "2026-10-29", "-o", str(dossier / sortie), *extra]
    )


def _texte(chemin):
    return "\n".join(p.extract_text() for p in PdfReader(chemin).pages)


# ---------- verifier ----------

def test_verifier_sort_en_erreur_si_infraction(tmp_path, capsys):
    (tmp_path / "a.md").write_text("contact@exemple.fr")
    assert main(["verifier", str(tmp_path)]) == 1


def test_verifier_affiche_fichier_ligne_et_extrait(tmp_path, capsys):
    (tmp_path / "a.md").write_text("propre\n\nÉcrire à contact@exemple.fr pour tout.\n")
    main(["verifier", str(tmp_path)])
    sortie = capsys.readouterr().out
    assert f"{tmp_path / 'a.md'}:3" in sortie
    assert "contact@exemple.fr" in sortie
    assert "courriel" in sortie


def test_verifier_sort_en_succes_sur_un_depot_propre(tmp_path, capsys):
    (tmp_path / "a.md").write_text("rien à signaler\n")
    assert main(["verifier", str(tmp_path)]) == 0
    assert capsys.readouterr().out.strip() != ""  # il dit ce qu'il a fait


def test_verifier_utilise_des_motifs_alternatifs(tmp_path, capsys):
    (tmp_path / "a.md").write_text("Jean Dupont\n")
    assert main(["verifier", str(tmp_path)]) == 0  # le fichier du kit ne contient aucun nom
    motifs = tmp_path / "motifs.yml"
    motifs.write_text('noms: ["Jean Dupont"]\n')
    assert main(["verifier", str(tmp_path), "--motifs", str(motifs)]) == 1


def test_verifier_racine_absente(tmp_path, capsys):
    assert main(["verifier", str(tmp_path / "absent")]) == 2
    assert "absent" in capsys.readouterr().err


# ---------- pdf ----------

def test_pdf_complet_et_trous(cours_dir):
    assert _pdf(cours_dir, mode="complet", sortie="c.pdf") == 0
    assert _pdf(cours_dir, mode="trous", sortie="t.pdf") == 0
    assert "SECRET" in _texte(cours_dir / "c.pdf")
    assert "SECRET" not in _texte(cours_dir / "t.pdf")
    for nom in ("c.pdf", "t.pdf"):
        assert "v1.02 du 29.10.26" in _texte(cours_dir / nom)


def test_pdf_cartouche_dit_le_type_de_document(cours_dir):
    _pdf(cours_dir, mode="trous", sortie="t.pdf")
    assert "COURS À TROUS" in _texte(cours_dir / "t.pdf").upper()


def test_pdf_resout_les_images_depuis_le_dossier_du_cours(cours_dir):
    (cours_dir / "slides" / "img").mkdir(parents=True)
    (cours_dir / "slides" / "img" / "s.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="200" height="30">'
        '<text x="2" y="20">DANS-IMAGE</text><text class="remplissable" x="90" y="20">REPONSE-IMG</text></svg>'
    )
    (cours_dir / "COURS.md").write_text("![s](slides/img/s.svg)\n")
    _pdf(cours_dir, mode="complet", sortie="c.pdf")
    _pdf(cours_dir, mode="trous", sortie="t.pdf")
    assert "REPONSE-IMG" in _texte(cours_dir / "c.pdf")
    assert "DANS-IMAGE" in _texte(cours_dir / "t.pdf")
    assert "REPONSE-IMG" not in _texte(cours_dir / "t.pdf")


def test_pdf_config_explicite(cours_dir, tmp_path):
    ailleurs = tmp_path / "autre.yml"
    (cours_dir / "cours.yml").rename(ailleurs)
    assert _pdf(cours_dir) == 2  # config par défaut absente
    assert _pdf(cours_dir, "--config", str(ailleurs)) == 0


@pytest.mark.parametrize("version", ["1.02", "v1.2", "v1.02-rc", "v1.02\n", ""])
def test_pdf_refuse_une_version_mal_formee(cours_dir, capsys, version):
    with pytest.raises(SystemExit) as e:
        main(["pdf", str(cours_dir / "COURS.md"), "--mode", "trous", "--version", version,
              "--date", "2026-10-29", "-o", str(cours_dir / "x.pdf")])
    assert e.value.code == 2
    assert "version" in capsys.readouterr().err
    assert not (cours_dir / "x.pdf").exists()


def test_pdf_refuse_une_date_invalide(cours_dir, capsys):
    with pytest.raises(SystemExit) as e:
        main(["pdf", str(cours_dir / "COURS.md"), "--mode", "trous", "--version", "v1.02",
              "--date", "29.10.2026", "-o", str(cours_dir / "x.pdf")])
    assert e.value.code == 2 and "date" in capsys.readouterr().err


def test_pdf_mode_inconnu(cours_dir):
    with pytest.raises(SystemExit) as e:
        main(["pdf", str(cours_dir / "COURS.md"), "--mode", "corrige", "--version", "v1.02",
              "--date", "2026-10-29", "-o", "x.pdf"])
    assert e.value.code == 2


def test_pdf_le_mode_est_obligatoire(cours_dir):
    with pytest.raises(SystemExit):
        main(["pdf", str(cours_dir / "COURS.md"), "--version", "v1.02", "--date", "2026-10-29", "-o", "x.pdf"])


def test_pdf_image_absente_echoue_sans_pdf(cours_dir, capsys):
    (cours_dir / "COURS.md").write_text("![s](img/absente.svg)\n")
    assert _pdf(cours_dir) == 2
    assert "absente.svg" in capsys.readouterr().err
    assert not (cours_dir / "x.pdf").exists()


def test_pdf_trou_mal_forme_echoue_sans_pdf(cours_dir, capsys):
    (cours_dir / "COURS.md").write_text("Un <ins>SECRET non refermé.\n")
    assert _pdf(cours_dir, mode="trous") == 2
    assert "ins" in capsys.readouterr().err
    assert not (cours_dir / "x.pdf").exists()


def test_pdf_config_invalide(cours_dir, capsys):
    (cours_dir / "cours.yml").write_text("titre: seul\n")
    assert _pdf(cours_dir) == 2
    assert "cours.yml" in capsys.readouterr().err


def test_pdf_source_absente(cours_dir, capsys):
    (cours_dir / "COURS.md").unlink()
    assert _pdf(cours_dir) == 2
    assert "COURS.md" in capsys.readouterr().err


# ---------- deck ----------

DECK = (
    "---\nmarp: true\nfooter: 'BTS CIEL-IR'\n---\n\n# C04 - Tableaux et vecteurs\n\n"
    "## Informatique - Prog Procédurale\n\n1CIELIR - Lycée Louis Rascol, Albi\n\n---\n\n## Deux\n"
)


def _deck(tmp_path, texte=DECK):
    """Un dépôt minimal : cours.yml à la racine, deck dans slides/."""
    (tmp_path / "slides").mkdir(exist_ok=True)
    shutil.copy(DONNEES / "cours-cpp.yml", tmp_path / "cours.yml")
    source = tmp_path / "slides" / "04-x.md"
    source.write_text(texte, encoding="utf-8")
    return source


def test_deck_injecte_la_version_dans_une_copie(tmp_path):
    source = _deck(tmp_path)
    sortie = tmp_path / "out" / "deck.md"
    sortie.parent.mkdir()
    assert main(["deck", str(source), "--version", "v1.02", "--date", "2026-10-29", "-o", str(sortie)]) == 0
    texte = sortie.read_text(encoding="utf-8")
    assert "v1.02 du 29.10.26" in texte and "Release : v1.02 (29.10.26)" in texte
    assert "https://github.com/ciel-ir-rascol/cpp-c04-tableauxVecteurs" in texte
    assert source.read_text(encoding="utf-8") == DECK  # la source n'est jamais modifiée


def test_deck_sans_entete_echoue(tmp_path, capsys):
    source = _deck(tmp_path, "# Pas d'en-tête\n")
    assert main(["deck", str(source), "--version", "v1.02", "--date", "2026-10-29", "-o", str(tmp_path / "d.md")]) == 2
    assert "en-tête" in capsys.readouterr().err
    assert not (tmp_path / "d.md").exists()


def test_deck_dont_le_titre_diverge_arrete_la_publication(tmp_path, capsys):
    source = _deck(tmp_path, DECK.replace("# C04 - Tableaux et vecteurs", "# Tableaux"))
    assert main(["deck", str(source), "--version", "v1.02", "--date", "2026-10-29", "-o", str(tmp_path / "d.md")]) == 2
    assert "cours.yml" in capsys.readouterr().err and not (tmp_path / "d.md").exists()


def test_deck_refuse_une_version_mal_formee(tmp_path, capsys):
    source = _deck(tmp_path)
    with pytest.raises(SystemExit) as e:
        main(["deck", str(source), "--version", "v1", "--date", "2026-10-29", "-o", str(tmp_path / "d.md")])
    assert e.value.code == 2 and not (tmp_path / "d.md").exists()
