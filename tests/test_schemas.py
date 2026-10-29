"""Les étiquettes `.remplissable` d'un schéma SVG ne doivent jamais atteindre le PDF à trous.

WeasyPrint n'applique pas la feuille du document aux éléments d'un `<svg>` : le masquage
par CSS ne suffit donc pas. Il y a trois chemins par où un SVG entre dans un document, et
chacun a son test : le SVG en ligne, le SVG chargé comme image (`<img>`, fond CSS, données
`data:`), et le SVG qui en référence un autre.
"""

import base64

import pytest
from pypdf import PdfReader

from cielircours.mdtext import Mode
from cielircours.rendu import _FetcherStrict, ecrire_pdf, rendre_html
from cielircours.schemas import filtrer_svg

NS = "http://www.w3.org/2000/svg"
SECRET = "REPONSE-SECRETE"


def _svg(interieur: str, racine: str = "") -> str:
    return f'<svg xmlns="{NS}" width="240" height="60" {racine}>{interieur}</svg>'


def _texte(tmp_path, source, mode, cours, pub) -> str:
    sortie = tmp_path / f"{mode.value}.pdf"
    ecrire_pdf(rendre_html(source, cours, pub, mode), tmp_path, sortie, mode)
    return "\n".join(p.extract_text() for p in PdfReader(sortie).pages)


def _controler(tmp_path, source, cours, pub, visible="STRUCTURE"):
    """Complet : tout y est. Trous : la structure reste, la réponse a disparu."""
    complet = _texte(tmp_path, source, Mode.COMPLET, cours, pub)
    assert SECRET in complet and visible in complet, complet
    trous = _texte(tmp_path, source, Mode.TROUS, cours, pub)
    assert SECRET not in trous, trous
    assert visible in trous, trous


# ---------- SVG en ligne ----------

def test_svg_en_ligne(tmp_path, cours, pub):
    source = "<p>" + _svg(
        f'<text x="5" y="20">STRUCTURE</text><text class="remplissable" x="5" y="40">{SECRET}</text>'
    ) + "</p>"
    _controler(tmp_path, source, cours, pub)


def test_svg_en_ligne_etiquette_a_plusieurs_classes(tmp_path, cours, pub):
    source = _svg(
        f'<text x="5" y="20">STRUCTURE</text><text class="etiquette remplissable gras" x="5" y="40">{SECRET}</text>'
    )
    _controler(tmp_path, source, cours, pub)


def test_svg_en_ligne_groupe_et_tspan(tmp_path, cours, pub):
    source = _svg(
        f'<text x="5" y="20">STRUCTURE</text>'
        f'<g class="remplissable"><rect width="9" height="9"/><text x="5" y="40">{SECRET}</text></g>'
    )
    _controler(tmp_path, source, cours, pub)
    source = _svg(f'<text x="5" y="20">STRUCTURE <tspan class="remplissable">{SECRET}</tspan></text>')
    _controler(tmp_path, source, cours, pub)


def test_un_enfant_ne_peut_pas_reafficher_la_reponse(tmp_path, cours, pub):
    """`visibility` s'hérite mais un enfant peut la rétablir : on retire, on ne masque pas."""
    source = _svg(
        '<text x="5" y="20">STRUCTURE</text>'
        f'<g class="remplissable" visibility="hidden"><text visibility="visible" x="5" y="40">{SECRET}</text></g>'
    )
    _controler(tmp_path, source, cours, pub)


def test_le_texte_qui_suit_un_svg_en_ligne_est_conserve(tmp_path, cours, pub):
    source = "<p>" + _svg(f'<text class="remplissable" x="5" y="20">{SECRET}</text>') + " SUITE-DU-PARAGRAPHE</p>"
    _controler(tmp_path, source, cours, pub, visible="SUITE-DU-PARAGRAPHE")


def test_une_classe_qui_ressemble_ne_retire_rien(tmp_path, cours, pub):
    source = _svg('<text class="remplissables" x="5" y="20">STRUCTURE</text>')
    assert "STRUCTURE" in _texte(tmp_path, source, Mode.TROUS, cours, pub)


def test_svg_en_ligne_depuis_le_markdown(tmp_path, cours, pub):
    """Le SVG passe par markdown-it comme n'importe quel HTML en bloc."""
    source = "Avant\n\n" + _svg(
        f'<text x="5" y="20">STRUCTURE</text><text class="remplissable" x="5" y="40">{SECRET}</text>'
    ) + "\n\nAprès\n"
    _controler(tmp_path, source, cours, pub)


# ---------- SVG chargé comme image ----------

def _ecrire(tmp_path, nom, contenu):
    (tmp_path / "img").mkdir(exist_ok=True)
    (tmp_path / "img" / nom).write_text(contenu, encoding="utf-8")


CORPS = f'<text x="5" y="20">STRUCTURE</text><text class="remplissable" x="5" y="40">{SECRET}</text>'


def test_svg_charge_par_img_markdown(tmp_path, cours, pub):
    _ecrire(tmp_path, "schema.svg", _svg(CORPS))
    _controler(tmp_path, "![schéma](img/schema.svg)", cours, pub)


def test_svg_charge_par_img_html(tmp_path, cours, pub):
    _ecrire(tmp_path, "schema.svg", _svg(CORPS))
    _controler(tmp_path, '<p><img src="img/schema.svg" width="200"></p>', cours, pub)


def test_svg_charge_par_img_avec_entete_xml_et_doctype(tmp_path, cours, pub):
    _ecrire(
        tmp_path,
        "schema.svg",
        '<?xml version="1.0" encoding="UTF-8"?>\n<!-- Inkscape -->\n' + _svg(CORPS, 'xmlns:xlink="http://www.w3.org/1999/xlink"'),
    )
    _controler(tmp_path, "![schéma](img/schema.svg)", cours, pub)


def test_svg_dont_l_extension_ment(tmp_path, cours, pub):
    """WeasyPrint essaie le SVG en dernier recours : on regarde le contenu, pas le nom."""
    _ecrire(tmp_path, "schema.png", _svg(CORPS))
    _controler(tmp_path, "![schéma](img/schema.png)", cours, pub)


def test_svg_en_donnees_base64(tmp_path, cours, pub):
    b64 = base64.b64encode(_svg(CORPS).encode()).decode()
    # markdown-it refuse les URL data: de type SVG : on passe par du HTML
    _controler(tmp_path, f'<img src="data:image/svg+xml;base64,{b64}" width="240">', cours, pub)


def test_svg_en_fond_css(tmp_path):
    """WeasyPrint ne dessine pas le texte d'un SVG de fond : on vérifie ce que reçoit le moteur."""
    _ecrire(tmp_path, "schema.svg", _svg(CORPS))
    url = (tmp_path / "img" / "schema.svg").as_uri()
    assert SECRET.encode() in _FetcherStrict(Mode.COMPLET).fetch(url).read()
    recu = _FetcherStrict(Mode.TROUS).fetch(url).read()
    assert SECRET.encode() not in recu and b"STRUCTURE" in recu
    assert _FetcherStrict(Mode.TROUS).fetch(url).content_type == "image/svg+xml"


def test_le_fond_css_svg_passe_bien_par_le_recuperateur(tmp_path, cours, pub, monkeypatch):
    _ecrire(tmp_path, "schema.svg", _svg(CORPS))
    vus = []
    original = _FetcherStrict.fetch
    monkeypatch.setattr(_FetcherStrict, "fetch", lambda self, url, headers=None: vus.append(url) or original(self, url, headers))
    source = '<div style="width:240px;height:60px;background-image:url(img/schema.svg)">x</div>'
    _texte(tmp_path, source, Mode.TROUS, cours, pub)
    assert any(u.endswith("img/schema.svg") for u in vus)


def test_svg_qui_en_charge_un_autre(tmp_path, cours, pub):
    _ecrire(tmp_path, "interieur.svg", _svg(CORPS))
    _ecrire(
        tmp_path,
        "enveloppe.svg",
        f'<svg xmlns="{NS}" width="240" height="60"><image href="interieur.svg" width="240" height="60"/></svg>',
    )
    _controler(tmp_path, "![schéma](img/enveloppe.svg)", cours, pub)


def test_svg_charge_par_embed(tmp_path, cours, pub):
    _ecrire(tmp_path, "schema.svg", _svg(CORPS))
    _controler(tmp_path, '<embed src="img/schema.svg" type="image/svg+xml" width="240" height="60">', cours, pub)


# ---------- le filtre lui-même ----------

def test_le_filtre_retire_les_etiquettes():
    sortie = filtrer_svg(_svg(CORPS).encode())
    assert SECRET.encode() not in sortie and b"STRUCTURE" in sortie


def test_le_filtre_ne_touche_pas_un_svg_sans_etiquette():
    brut = _svg('<text x="5" y="20">STRUCTURE</text>').encode()
    assert filtrer_svg(brut) is brut


@pytest.mark.parametrize(
    "brut",
    [b"\x89PNG\r\n\x1a\n\x00\x00", b"wOF2\x00\x01", b"body { color: red }", b"", b"<html><p class='remplissable'>x</p></html>", b"<svg"],
)
def test_le_filtre_laisse_passer_ce_qui_n_est_pas_un_svg(brut):
    assert filtrer_svg(brut) is brut


def test_le_filtre_accepte_un_bom_utf8():
    sortie = filtrer_svg(b"\xef\xbb\xbf" + _svg(CORPS).encode())
    assert SECRET.encode() not in sortie


def test_le_filtre_garde_les_accents():
    brut = _svg('<text x="5" y="20">Entrée / Sortie</text><text class="remplissable">x</text>').encode()
    assert "Entrée / Sortie".encode() in filtrer_svg(brut)


def test_un_svg_entierement_remplissable_ne_montre_rien():
    sortie = filtrer_svg(f'<svg xmlns="{NS}" class="remplissable" width="9" height="9"><text>{SECRET}</text></svg>'.encode())
    assert SECRET.encode() not in sortie


def test_ecrire_pdf_exige_un_mode(tmp_path, cours, pub):
    with pytest.raises(TypeError, match="Mode"):
        ecrire_pdf(rendre_html("x", cours, pub, Mode.TROUS), tmp_path, tmp_path / "x.pdf", "trous")
