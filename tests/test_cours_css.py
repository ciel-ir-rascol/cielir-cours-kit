import re
from itertools import combinations
from pathlib import Path

import pytest
from pypdf import PdfReader
from weasyprint import HTML

from cielircours.config import lire_config
from cielircours.mdtext import Mode
from cielircours.rendu import Publication, ecrire_pdf, rendre_html
from outils import (
    COURS_CSS,
    DONNEES,
    boites,
    contraste,
    debordement_horizontal,
    fonds_des_encadres,
    luminances_des_fonds,
    pages_rendues,
    regle,
)

POLICES = COURS_CSS.parent / "polices"
FICHE = (DONNEES / "fiche-exemple.md").read_text(encoding="utf-8")


def test_les_encadres_restent_distincts_en_niveaux_de_gris():
    fonds = luminances_des_fonds(COURS_CSS)
    assert set(fonds) == {f"alerte--{t}" for t in ("note", "astuce", "important", "attention", "danger")}
    for a, b in combinations(fonds.values(), 2):
        assert abs(a - b) >= 8  # ΔL* minimal entre deux fonds d'encadré


def test_le_texte_garde_son_contraste_sur_chaque_encadre():
    for classe, fond in fonds_des_encadres(COURS_CSS).items():
        assert contraste("#000000", fond) >= 7, classe


def test_l_outil_de_luminance_mesure_vraiment(tmp_path):
    css = tmp_path / "t.css"
    css.write_text(".alerte--note { background: #ffffff; }\n.alerte--danger { background-color: #000; }")
    fonds = luminances_des_fonds(css)
    assert fonds["alerte--note"] == pytest.approx(100, abs=0.1)
    assert fonds["alerte--danger"] == pytest.approx(0, abs=0.1)


def test_rien_ne_se_coupe_entre_deux_pages():
    css = COURS_CSS.read_text(encoding="utf-8")
    for sel in (".trou", ".lignes", ".bande", ".alerte", "table"):
        assert "break-inside: avoid" in regle(css, sel), sel


def test_un_bandeau_n_est_jamais_seul_en_bas_de_page():
    css = COURS_CSS.read_text(encoding="utf-8")
    assert "break-after: avoid" in regle(css, ".bande")


def test_les_etiquettes_remplissables_disparaissent_en_mode_trous():
    css = COURS_CSS.read_text(encoding="utf-8")
    assert "body.mode-trous .remplissable" in css
    assert "visibility: hidden" in regle(css, "body.mode-trous .remplissable")


def test_les_polices_sont_locales():
    css = COURS_CSS.read_text(encoding="utf-8")
    assert "https://" not in css and "http://" not in css
    assert list(POLICES.glob("*.woff2"))
    for nom in re.findall(r'url\("?([^")]+)"?\)', css):
        assert (COURS_CSS.parent / nom).is_file(), nom


def test_les_licences_des_polices_sont_documentees():
    texte = (POLICES / "LICENCES.md").read_text(encoding="utf-8")
    for attendu in ("Liberation Sans", "Inconsolata", "SIL Open Font License 1.1", "https://github.com"):
        assert attendu in texte


def test_une_seule_declaration_de_page(cours, pub):
    html = rendre_html("# T", cours, pub, Mode.TROUS)
    assert "@page" not in html  # le gabarit ne câble plus la page : tout est dans cours.css
    assert len(re.findall(r"@page\s*{", COURS_CSS.read_text(encoding="utf-8"))) >= 1
    assert "cours.css" in html


def test_un_trou_long_ne_deborde_pas(tmp_path):  # Review Focus 2
    long = "une phrase entière de réponse qui ne tient pas sur une ligne"
    pages = pages_rendues(f"Réponse : <ins>{long}</ins>.", Mode.TROUS, tmp_path)
    assert len(boites(pages, "trou")) == 1  # il y a bien un trou à mesurer
    assert debordement_horizontal(pages) == []


def test_un_trou_tres_long_dans_un_tableau_ne_deborde_pas(tmp_path):
    long = "une réponse démesurée " * 8
    source = f"| a | b |\n| --- | --- |\n| <ins>{long}</ins> | x |\n"
    pages = pages_rendues(source, Mode.TROUS, tmp_path)
    assert len(boites(pages, "trou")) == 1
    assert debordement_horizontal(pages) == []


def test_l_outil_de_debordement_detecte_un_debordement():
    html = "<style>@page{size:A4;margin:1.5cm}</style><div class='large' style='width:30cm'>x</div>"
    pages = HTML(string=html).render().pages
    assert debordement_horizontal(pages) != []
    assert debordement_horizontal(HTML(string="<style>@page{size:A4}</style><p>x</p>").render().pages) == []


def test_un_trou_est_proportionnel_a_sa_reponse(tmp_path):
    pages = pages_rendues("<ins>ab</ins> <ins>abcdefghijklmnopqrst</ins>", Mode.TROUS, tmp_path)
    (_, court), (_, long) = boites(pages, "trou")
    assert long.margin_width() > court.margin_width() + 50


def _longue_fiche(repetitions: int) -> str:
    return "\n\n".join(FICHE for _ in range(repetitions))


def test_aucun_element_a_ecrire_n_est_coupe(tmp_path):
    pages = pages_rendues(_longue_fiche(3), Mode.TROUS, tmp_path)
    assert len(pages) >= 4  # il y a bien des sauts de page à éprouver
    lignes = boites(pages, "lignes")
    assert len(lignes) >= 6
    pas = {round(b.height / n, 1) for _, b in lignes for n in [int(b.element.get("style").split("--n:")[1].rstrip(";"))]}
    assert len(pas) == 1 and min(pas) >= 18  # hauteur complète partout, et la place d'écrire à la main
    # aucun bandeau n'est le dernier élément de sa page
    for i, page in enumerate(pages):
        racine = page._page_box.children[0]
        corps = [b for b in racine.descendants() if type(b).__name__ == "TextBox"]
        for _, bande in (x for x in boites(pages, "bande") if x[0] == i):
            apres = [t for t in corps if t.position_y > bande.position_y + bande.height - 1]
            assert apres, f"bandeau orphelin en bas de la page {i + 1}"


def test_l_interligne_est_plus_large_en_mode_trous():
    css = COURS_CSS.read_text(encoding="utf-8")
    complet = re.search(r"line-height:\s*([\d.]+)", regle(css, "body"))
    trous = re.search(r"line-height:\s*([\d.]+)", regle(css, "body.mode-trous"))
    assert complet and trous and float(trous.group(1)) > float(complet.group(1))


@pytest.mark.parametrize("mode", [Mode.COMPLET, Mode.TROUS])
def test_la_fiche_tient_en_trois_pages_au_plus(tmp_path, mode):
    pages = pages_rendues(FICHE, mode, tmp_path)
    assert len(pages) <= 3
    assert debordement_horizontal(pages) == []


def test_les_polices_sont_embarquees_dans_le_pdf(tmp_path, cours, pub):
    html = rendre_html(FICHE, cours, pub, Mode.TROUS)
    sortie = tmp_path / "f.pdf"
    ecrire_pdf(html, tmp_path, sortie)
    polices = {}
    for page in PdfReader(sortie).pages:
        for f in page["/Resources"].get("/Font", {}).values():
            f = f.get_object()
            desc = f["/DescendantFonts"][0].get_object()["/FontDescriptor"] if "/DescendantFonts" in f else f["/FontDescriptor"]
            polices[str(f["/BaseFont"])] = {"/FontFile2", "/FontFile3", "/FontFile"} & set(desc.get_object())
    assert any("Liberation" in n for n in polices) and any("Inconsolata" in n for n in polices), polices
    assert all(polices.values()), polices  # chaque police a son fichier embarqué


def _texte_pdf(tmp_path, source, mode, cours, pub):
    sortie = tmp_path / f"{mode.value}.pdf"
    ecrire_pdf(rendre_html(source, cours, pub, mode), tmp_path, sortie)
    return "\n".join(p.extract_text() for p in PdfReader(sortie).pages)


def test_une_etiquette_remplissable_html_est_absente_du_pdf_a_trous(tmp_path, cours, pub):
    source = '<p>Avant <span class="remplissable">ETIQUETTE-SECRETE</span> après</p>'
    assert "ETIQUETTE-SECRETE" in _texte_pdf(tmp_path, source, Mode.COMPLET, cours, pub)
    assert "ETIQUETTE-SECRETE" not in _texte_pdf(tmp_path, source, Mode.TROUS, cours, pub)


@pytest.mark.xfail(
    strict=True,
    reason="WeasyPrint n'applique pas la feuille du document aux éléments d'un <svg> en ligne : "
    "la règle .remplissable ne masque pas encore les étiquettes d'un schéma. À traiter par le "
    "convertisseur (tâche 9) : injecter un <style> dans le SVG en mode trous.",
)
def test_une_etiquette_remplissable_de_svg_est_absente_du_pdf_a_trous(tmp_path, cours, pub):
    source = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="200" height="40">'
        '<text class="remplissable" x="5" y="20">ETIQUETTE-SVG</text></svg>'
    )
    assert "ETIQUETTE-SVG" not in _texte_pdf(tmp_path, source, Mode.TROUS, cours, pub)
