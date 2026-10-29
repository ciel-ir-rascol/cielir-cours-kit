from importlib.resources import files
from pathlib import Path

import pytest

from cielircours.confidentialite import Infraction, controler

MOTIFS = Path(str(files("cielircours.donnees") / "motifs.yml"))


def ecrire(racine: Path, nom: str, texte: str) -> Path:
    chemin = racine / nom
    chemin.parent.mkdir(parents=True, exist_ok=True)
    chemin.write_text(texte, encoding="utf-8")
    return chemin


def motifs_de(racine: Path) -> list[str]:
    return [i.motif for i in controler(racine, MOTIFS)]


# --- ce qui doit être attrapé ---------------------------------------------

def test_detecte_une_adresse_de_courriel(tmp_path):
    ecrire(tmp_path, "slides.md", "📧 [prof.fictif@lycee-fictif.fr](mailto:prof.fictif@lycee-fictif.fr)")
    assert motifs_de(tmp_path) == ["courriel", "courriel"]


def test_detecte_une_adresse_dans_un_attribut_html(tmp_path):
    ecrire(tmp_path, "page.html", '<a href="mailto:prof.fictif@lycee-fictif.fr">Contact</a>')
    assert motifs_de(tmp_path) == ["courriel"]


def test_detecte_une_adresse_dans_un_texte(tmp_path):
    ecrire(tmp_path, "a.md", "Écrire à prof.fictif+cours@sous.lycee-fictif.fr pour toute question.")
    infractions = controler(tmp_path, MOTIFS)
    assert [i.motif for i in infractions] == ["courriel"]


@pytest.mark.parametrize(
    "texte",
    [
        "Tel : 06 00 00 00 00",
        "Tel : 06.00.00.00.00",
        "Tel : 06-00-00-00-00",
        "Tel : +33 6 00 00 00 00",
        "Tel : +33600000000",
        "Tel : 0033 6 00 00 00 00",
        "Tel : 05 63 00 00 00",
        "Tel : 0600000000",
        "Tel:0600000000.",
    ],
)
def test_detecte_un_telephone_francais(tmp_path, texte):
    ecrire(tmp_path, "a.md", texte)
    assert motifs_de(tmp_path) == ["telephone"]


def test_infraction_porte_fichier_ligne_motif_et_extrait(tmp_path):
    chemin = ecrire(tmp_path, "sous/a.md", "une ligne\nTel : 06 00 00 00 00\n")
    [i] = controler(tmp_path, MOTIFS)
    assert i == Infraction(fichier=chemin, ligne=2, motif="telephone", extrait="Tel : 06 00 00 00 00")


@pytest.mark.parametrize("avant, apres", [(0, 200), (200, 200), (200, 0), (10, 10)])
def test_extrait_limite_a_80_caracteres_et_contient_l_occurrence(tmp_path, avant, apres):
    ecrire(tmp_path, "a.md", "x " * (avant // 2) + "prof.fictif@lycee-fictif.fr" + " y" * (apres // 2))
    [i] = controler(tmp_path, MOTIFS)
    assert len(i.extrait) <= 80
    assert "prof.fictif@lycee-fictif.fr" in i.extrait


def test_extrait_d_un_telephone_en_fin_de_longue_ligne(tmp_path):
    ecrire(tmp_path, "a.md", "mot " * 60 + "06 00 00 00 00")
    [i] = controler(tmp_path, MOTIFS)
    assert i.extrait.endswith("06 00 00 00 00") and len(i.extrait) <= 80


def test_une_occurrence_une_infraction(tmp_path):
    ecrire(tmp_path, "a.md", "a@lycee-fictif.fr et b@lycee-fictif.fr\nc@lycee-fictif.fr")
    assert [(i.ligne, i.motif) for i in controler(tmp_path, MOTIFS)] == [
        (1, "courriel"), (1, "courriel"), (2, "courriel"),
    ]


def test_les_noms_configures_sont_detectes(tmp_path):
    motifs = ecrire(tmp_path, "m.yml", "courriel: {expression: 'zzz'}\ntelephone: {expression: 'zzz'}\nnoms: [Dupont Fictif]\n")
    depot = tmp_path / "depot"
    ecrire(depot, "a.md", "Cours de DUPONT fictif, Albi")
    assert [i.motif for i in controler(depot, motifs)] == ["nom_enseignant"]


def test_noms_vides_ne_detecte_aucun_nom(tmp_path):
    ecrire(tmp_path, "a.md", "Cours de Dupont Fictif")
    assert controler(tmp_path, MOTIFS) == []


# --- ce qui ne doit pas être attrapé ---------------------------------------

def test_un_etablissement_n_est_pas_une_infraction(tmp_path):
    ecrire(tmp_path, "a.md", "Lycée Louis Rascol, Albi — BTS CIEL-IR, 1re année")
    assert controler(tmp_path, MOTIFS) == []


@pytest.mark.parametrize(
    "texte",
    [
        "Écrire à prenom.nom@example.org",
        "Écrire à prenom.nom@example.com ou x@sous.example.net",
        "admin@serveur.invalid, a@b.test",
        "Un décorateur @property et @pytest.fixture",
    ],
)
def test_une_adresse_d_exemple_n_est_pas_une_infraction(tmp_path, texte):
    ecrire(tmp_path, "a.md", texte)
    assert controler(tmp_path, MOTIFS) == []


@pytest.mark.parametrize(
    "texte",
    [
        "date : 2026-10-29 et 29/10/2026",
        "horodatage 1700000000, uid=1000(eleve) gid=1000",
        "int mode = 0755; int m = 01234567;",
        "suite 012345678901234 et 2006000000003",
        "ip 192.168.100.10, masque 255.255.255.0",
        "build 20261029123456 et 1006000000003 (sans rapport)",
        "version 1.06.00.00.00.00",
        "identifiant a06 00 00 00 00b",
    ],
)
def test_un_numero_qui_n_en_est_pas_un_n_est_pas_une_infraction(tmp_path, texte):
    ecrire(tmp_path, "a.md", texte)
    assert controler(tmp_path, MOTIFS) == []


# --- périmètre ---------------------------------------------------------------

def test_git_est_ignore(tmp_path):
    ecrire(tmp_path, ".git/config", "email = prof.fictif@lycee-fictif.fr")
    assert controler(tmp_path, MOTIFS) == []


@pytest.mark.parametrize("dossier", [".git", ".venv", "node_modules", "__pycache__", "_site", "dist"])
def test_dossiers_lourds_ignores_par_defaut(tmp_path, dossier):
    ecrire(tmp_path, f"{dossier}/sous/a.md", "x@lycee-fictif.fr")
    assert controler(tmp_path, MOTIFS) == []


def test_cielir_ignore_exclut_un_fichier_et_un_dossier(tmp_path):
    ecrire(tmp_path, ".cielir-ignore", "# commentaire\n\nvendor\nnotes/prive.md\n*.log\n")
    ecrire(tmp_path, "vendor/lib/a.md", "x@lycee-fictif.fr")
    ecrire(tmp_path, "notes/prive.md", "x@lycee-fictif.fr")
    ecrire(tmp_path, "debug.log", "x@lycee-fictif.fr")
    ecrire(tmp_path, "notes/public.md", "x@lycee-fictif.fr")
    assert [i.fichier.name for i in controler(tmp_path, MOTIFS)] == ["public.md"]


def test_fichier_binaire_ignore(tmp_path):
    (tmp_path / "img.png").write_bytes(b"\x89PNG\x00\x00x@lycee-fictif.fr\xff\xfe")
    assert controler(tmp_path, MOTIFS) == []


def test_parcourt_les_sous_dossiers(tmp_path):
    ecrire(tmp_path, "a/b/c.md", "x@lycee-fictif.fr")
    assert [i.fichier for i in controler(tmp_path, MOTIFS)] == [tmp_path / "a/b/c.md"]


# --- ronde 2 : faux positifs courants dans les TP -----------------------------

@pytest.mark.parametrize(
    "texte",
    [
        "git clone git@github.com:organisation/depot.git",
        "ssh eleve@192.168.100.10",
        "scp fichier eleve@serveur.lan:/tmp",
        "ssh eleve@d116-01.salle.local",
        "ssh eleve@bastion.interne.internal",
        "![logo](images/logo@2x.png)",
        "ssh root@localhost",
    ],
)
def test_une_connexion_ssh_ou_une_image_n_est_pas_un_courriel(tmp_path, texte):
    ecrire(tmp_path, "a.md", texte)
    assert controler(tmp_path, MOTIFS) == []


def test_une_adresse_reelle_a_cote_d_une_connexion_ssh_reste_detectee(tmp_path):
    ecrire(tmp_path, "a.md", "ssh eleve@192.168.100.10 puis écrire à prof.fictif@lycee-fictif.fr")
    assert motifs_de(tmp_path) == ["courriel"]


@pytest.mark.parametrize(
    "texte",
    [
        "05.03.2026 14:00",
        "08-00-27-12-34-56",
        "08:00:27:12:34:56",
        "01 02 03 04 05 06",
        "06 00-00 00.00",
    ],
)
def test_des_paires_de_chiffres_qui_ne_sont_pas_un_numero(tmp_path, texte):
    ecrire(tmp_path, "a.md", texte)
    assert controler(tmp_path, MOTIFS) == []


@pytest.mark.parametrize(
    "texte",
    [
        "Tel : +33 (0)6 00 00 00 00",
        "Tel : +33 (0)6.00.00.00.00",
        "Tel : +33(0)600000000",
        "Tel : 06 00 00 00 00 (bureau)",
        "Tel:06-00-00-00-00",
    ],
)
def test_notations_francaises_courantes_detectees(tmp_path, texte):
    ecrire(tmp_path, "a.md", texte)
    assert motifs_de(tmp_path) == ["telephone"]


def test_deux_numeros_sur_une_ligne_font_deux_infractions(tmp_path):
    ecrire(tmp_path, "a.md", "06 00 00 00 00, 05 63 00 00 00")
    assert motifs_de(tmp_path) == ["telephone", "telephone"]


def test_fichier_cp1252_est_controle(tmp_path):
    (tmp_path / "ancien.txt").write_bytes("Contact : prof.fictif@lycee-fictif.fr (accentué é)".encode("cp1252"))
    assert motifs_de(tmp_path) == ["courriel"]


def test_fichier_utf8_avec_un_octet_invalide_est_controle(tmp_path):
    (tmp_path / "a.txt").write_bytes(b"debut \xff fin 06 00 00 00 00")
    assert motifs_de(tmp_path) == ["telephone"]


def test_fichier_utf16_avec_bom_est_controle(tmp_path):
    (tmp_path / "a.txt").write_bytes("prof.fictif@lycee-fictif.fr".encode("utf-16"))
    assert motifs_de(tmp_path) == ["courriel"]


def test_les_noms_ont_des_bornes_de_mot(tmp_path):
    motifs = ecrire(tmp_path, "m.yml", "noms: [Roux]\n")
    depot = tmp_path / "depot"
    ecrire(depot, "a.md", "Le nombre de Rouxel, prénom Rouxe.\nCours de Roux.")
    assert [(i.ligne, i.motif) for i in controler(depot, motifs)] == [(2, "nom_enseignant")]


def test_cielir_ignore_avec_bom_est_lu(tmp_path):
    (tmp_path / ".cielir-ignore").write_bytes("\ufeffvendor\n".encode("utf-8"))
    ecrire(tmp_path, "vendor/a.md", "x@lycee-fictif.fr")
    ecrire(tmp_path, "b.md", "propre")
    assert controler(tmp_path, MOTIFS) == []


def test_cielir_ignore_non_utf8_ne_plante_pas(tmp_path):
    (tmp_path / ".cielir-ignore").write_bytes(b"# \xe9t\xe9\nvendor\n")
    ecrire(tmp_path, "vendor/a.md", "x@lycee-fictif.fr")
    ecrire(tmp_path, "b.md", "x@lycee-fictif.fr")
    assert [i.fichier.name for i in controler(tmp_path, MOTIFS)] == ["b.md"]


@pytest.mark.parametrize("motif", ["*", "**", "**/*"])
def test_un_cielir_ignore_qui_exclut_tout_avertit(tmp_path, motif):
    ecrire(tmp_path, ".cielir-ignore", motif + "\n")
    ecrire(tmp_path, "a.md", "x@lycee-fictif.fr")
    with pytest.warns(UserWarning, match="exclut tous les fichiers"):
        assert controler(tmp_path, MOTIFS) == []


def test_un_cielir_ignore_raisonnable_n_avertit_pas(tmp_path, recwarn):
    ecrire(tmp_path, ".cielir-ignore", "vendor\n")
    ecrire(tmp_path, "vendor/a.md", "x")
    ecrire(tmp_path, "b.md", "propre")
    controler(tmp_path, MOTIFS)
    assert len(recwarn) == 0
