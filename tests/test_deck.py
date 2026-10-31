from datetime import date
from pathlib import Path

import pytest

from dataclasses import replace

from cielircours.config import lire_config
from cielircours.deck import preparer_deck
from cielircours.rendu import Publication


def _prep(source, pub, cours=None):
    return preparer_deck(source, pub, cours or COURS)

PUB = Publication("v1.02", date(2026, 10, 29))
COURS = lire_config(Path(__file__).parent / "data" / "cours-cpp.yml")
LOGO = replace(COURS, logo="logo.svg")

ENTETE = """---
marp: true
theme: ciel
paginate: true
title: Introduction aux réseaux
{pied}---
"""

CORPS = """
<!-- _class: lead -->

# C04 - Tableaux et vecteurs

## Informatique - Prog Procédurale

1CIELIR - Lycée Louis Rascol, Albi

<!--
Notes de l'enseignant pour la première slide.
-->

---

## Le modèle OSI

| Couche | Rôle |
|---|---|
| 1 | Physique |

---

## Fin
"""

DECK = ENTETE.format(pied="footer: 'BTS CIEL-IR · Réseaux · 1re année'\n") + CORPS
DECK_SANS_PIED = ENTETE.format(pied="") + CORPS


def deck_avec_pied(ligne):
    return ENTETE.format(pied=ligne + "\n") + CORPS


def test_le_pied_recoit_la_version():
    sortie = _prep(DECK, PUB)
    assert "footer: 'BTS CIEL-IR · Réseaux · 1re année · v1.02 du 29.10.26'" in sortie


def test_la_premiere_slide_recoit_la_version():
    premiere = _prep(DECK, PUB).split("\n---\n")[1]
    assert "Release : v1.02 (29.10.26)" in premiere


def test_la_source_n_est_pas_modifiee():
    avant = DECK
    _prep(DECK, PUB)
    assert DECK == avant


def test_un_deck_sans_pied_en_recoit_un():
    sortie = _prep(DECK_SANS_PIED, PUB)
    assert "footer: 'v1.02 du 29.10.26'" in sortie
    assert sortie.split("\n---\n")[0].count("footer:") == 1


@pytest.mark.parametrize("ligne", [
    "footer: 'BTS CIEL-IR · Réseaux'",
    'footer: "BTS CIEL-IR · Réseaux"',
    "footer: BTS CIEL-IR · Réseaux",
])
def test_les_trois_ecritures_du_pied(ligne):
    sortie = _prep(deck_avec_pied(ligne), PUB)
    assert "footer: 'BTS CIEL-IR · Réseaux · v1.02 du 29.10.26'" in sortie
    assert sortie.count("footer:") == 1


def test_apostrophe_du_pied_conservee():
    sortie = _prep(deck_avec_pied('footer: "Cours d\'accueil"'), PUB)
    assert "footer: 'Cours d''accueil · v1.02 du 29.10.26'" in sortie


def test_le_reste_du_deck_est_intact():
    sortie = _prep(DECK, PUB)
    assert "## Le modèle OSI\n\n| Couche | Rôle |\n|---|---|\n| 1 | Physique |" in sortie
    assert sortie.endswith("## Fin\n")
    assert sortie.count("Release : v1.02") == 1


def test_la_ligne_est_dans_la_premiere_slide_avant_le_separateur():
    premiere = _prep(DECK, PUB).split("\n---\n")[1]
    assert premiere.rstrip().endswith("</div>") and "Release : v1.02 (29.10.26)" in premiere


TITRE = "# C04 - Tableaux et vecteurs\n\n## Informatique - Prog Procédurale\n\n1CIELIR - Lycée Louis Rascol, Albi\n"
RELEASE = "Release : v1.02 (29.10.26)"


def _deck_une_slide(contenu, suite=True):
    """Deck dont la première slide est la page de titre puis `contenu`, suivie d'une seconde slide."""
    corps = TITRE + "\n" + contenu + ("\n\n---\n\n## Deux\n" if suite else "\n")
    return ENTETE.format(pied="footer: 'X'\n") + "\n" + corps


def _dans_la_premiere_slide(sortie):
    """Vrai si l'unique ligne de release précède la seconde slide (repérée par son titre)."""
    suivante = "## Suite" if "## Suite" in sortie else "## Deux"
    return sortie.count(RELEASE) == 1 and sortie.index(RELEASE) < sortie.index(suivante)


def test_un_tiret_triple_dans_un_bloc_de_code_n_est_pas_un_separateur():
    deck = _deck_une_slide("```yaml\n---\nclef: valeur\n---\n```\n\nSuite de la première slide.")
    sortie = _prep(deck, PUB)
    premiere, deuxieme = sortie.split("\n---\n\n## Deux")[0], sortie.split("\n---\n\n## Deux")[1]
    assert RELEASE in premiere and "Release" not in deuxieme
    assert "clef: valeur\n---\n```" in sortie


def test_un_deck_a_une_seule_slide():
    sortie = _prep(_deck_une_slide("", suite=False), PUB)
    assert RELEASE in sortie and sortie.rstrip().endswith("</div>")
    assert "footer: 'X · v1.02 du 29.10.26'" in sortie


def test_la_page_de_titre_porte_la_release_et_le_lien_du_depot_et_rien_d_autre_d_injecte():
    sortie = _prep(DECK, PUB)
    assert ('<div class="pied-titre">\n\nRelease : v1.02 (29.10.26)\\\n'
            '🐙 <https://github.com/ciel-ir-rascol/cpp-c04-tableauxVecteurs>\n\n</div>') in sortie
    assert "@" not in sortie.split("\n---\n")[1]  # jamais de courriel sur la page de titre
    assert "logo" not in sortie.lower() and "style:" not in sortie  # pas de logo : rien d'injecté


def test_le_premier_du_mois_et_le_jour_a_deux_chiffres():
    assert "Release : v2.00 (01.01.27)" in _prep(DECK, Publication("v2.00", date(2027, 1, 1)))


def test_deck_sans_entete_refuse():
    with pytest.raises(ValueError):
        _prep("# Pas d'en-tête\n", PUB)


@pytest.mark.parametrize("contenu", [
    "# Titre\n---\n\n## Suite",
    "```text\ncode\n```\n---\n\n## Suite",
    "<!-- note -->\n---\n\n## Suite",
    "<!--\nnote\n-->\n---\n\n## Suite",
    "~~~text\n---\n~~~\n\nTexte",
    "```text\n---\n```\n\nTexte",
    "<!--\nNote\n\n---\n\nsuite de la note\n-->",
], ids=["titre-atx", "fin-de-code", "commentaire-colle", "commentaire-multiligne-colle",
        "tildes", "backticks", "commentaire-avec-vide-et-tirets"])
def test_la_release_va_toujours_dans_la_premiere_slide(contenu):
    sortie = _prep(_deck_une_slide(contenu), PUB)
    assert _dans_la_premiere_slide(sortie)


def test_la_release_n_est_pas_dans_un_commentaire():
    deck = _deck_une_slide("<!--\nNote\n\n---\n\nsuite\n-->")
    sortie = _prep(deck, PUB)
    assert sortie.index(RELEASE) > sortie.index("-->")


def test_un_titre_setext_n_est_pas_un_separateur():
    sortie = _prep(_deck_une_slide("Titre\n---\n\nSuite du texte"), PUB)
    assert "Suite du texte\n\n<div" in sortie
    assert _dans_la_premiere_slide(sortie)


def test_entete_non_referme_refuse():
    with pytest.raises(ValueError):
        _prep("---\nmarp: true\n\n# Titre\n", PUB)


# ---------- le logo ----------

def test_sans_logo_rien_n_est_injecte_hors_release():
    sortie = _prep(DECK, PUB)
    assert "--logo" not in sortie and "logo-titre" not in sortie and "style" not in sortie.split("\n---\n")[0]


def test_avec_logo_le_style_et_l_image_de_titre_sont_injectes():
    sortie = _prep(DECK, PUB, LOGO)
    entete = sortie.split("\n---\n")[0]
    assert "style: |\n  section { --logo: url('img/logo.svg'); --logo-reserve: 144px; }" in entete
    premiere = sortie.split("\n---\n")[1]
    assert premiere.index('<img class="logo-titre" src="img/logo.svg"') < premiere.index("# C04")


def test_un_style_deja_present_dans_l_entete_est_refuse_quand_il_y_a_un_logo():
    deck = DECK.replace("paginate: true\n", "paginate: true\nstyle: |\n  h1 { color: red }\n")
    with pytest.raises(ValueError, match="style"):
        _prep(deck, PUB, LOGO)
    assert "h1 { color: red }" in _prep(deck, PUB)  # sans logo, l'auteur reste libre


# ---------- le garde-fou : la page de titre doit dire ce que dit cours.yml ----------

@pytest.mark.parametrize(("ancien", "nouveau", "attendu"), [
    ("# C04 - Tableaux et vecteurs", "# C04 - Tableaux", "# C04 - Tableaux et vecteurs"),
    ("# C04 - Tableaux et vecteurs", "# Tableaux et vecteurs", "titre"),
    ("# C04 - Tableaux et vecteurs", "# C4 - Tableaux et vecteurs", "titre"),
    ("# C04 - Tableaux et vecteurs", "## C04 - Tableaux et vecteurs", "titre"),
    ("## Informatique - Prog Procédurale", "## Informatique - Prog Objet", "discipline et séquence"),
    ("1CIELIR - Lycée Louis Rascol, Albi", "1re année - Lycée Louis Rascol, Albi", "classe et établissement"),
    ("1CIELIR - Lycée Louis Rascol, Albi", "", "classe et établissement"),
])
def test_une_page_de_titre_qui_diverge_de_cours_yml_arrete_la_publication(ancien, nouveau, attendu):
    assert ancien in DECK
    with pytest.raises(ValueError, match="cours.yml") as e:
        _prep(DECK.replace(ancien, nouveau), PUB)
    assert attendu in str(e.value)


def test_le_message_dit_ce_qui_est_attendu_et_ce_qui_est_trouve():
    with pytest.raises(ValueError) as e:
        _prep(DECK.replace("# C04 - Tableaux et vecteurs", "# Cours 04"), PUB)
    assert "# C04 - Tableaux et vecteurs" in str(e.value) and "Cours 04" in str(e.value)


def test_le_titre_dans_un_commentaire_ne_compte_pas():
    deck = DECK.replace("# C04 - Tableaux et vecteurs", "<!-- # C04 - Tableaux et vecteurs -->\n# Autre")
    with pytest.raises(ValueError, match="titre"):
        _prep(deck, PUB)


def test_le_gabarit_de_deck_passe_le_garde_fou_une_fois_rempli():
    import re

    gabarit = (Path(__file__).resolve().parents[1] / "gabarits" / "deck.md").read_text(encoding="utf-8")
    gabarit = re.sub(r"<!--\nGabarit.*?-->\n\n", "", gabarit, count=1, flags=re.S)
    remplace = [
        ("C«NN» - «Titre de la séance»", COURS.titre_page),
        ("«Discipline» - «Libellé de la séquence»", f"{COURS.discipline} - {COURS.sequence_libelle}"),
        ("«1CIELIR» - «Établissement»", f"{COURS.classe} - {COURS.etablissement}"),
    ]
    for a, b in remplace:
        assert a in gabarit, a
        gabarit = gabarit.replace(a, b)
    sortie = _prep(gabarit, PUB)
    assert RELEASE in sortie
