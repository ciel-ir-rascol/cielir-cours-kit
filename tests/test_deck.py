from datetime import date

import pytest

from cielircours.deck import preparer_deck
from cielircours.rendu import Publication

PUB = Publication("v1.02", date(2026, 10, 29))

ENTETE = """---
marp: true
theme: ciel
paginate: true
title: Introduction aux réseaux
{pied}---
"""

CORPS = """
<!-- _class: lead -->

# Introduction aux réseaux

**1re année — Cours 03**

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
    sortie = preparer_deck(DECK, PUB)
    assert "footer: 'BTS CIEL-IR · Réseaux · 1re année · v1.02 du 29.10.26'" in sortie


def test_la_premiere_slide_recoit_la_version():
    premiere = preparer_deck(DECK, PUB).split("\n---\n")[1]
    assert "**v1.02** — 29 octobre 2026" in premiere


def test_la_source_n_est_pas_modifiee():
    avant = DECK
    preparer_deck(DECK, PUB)
    assert DECK == avant


def test_un_deck_sans_pied_en_recoit_un():
    sortie = preparer_deck(DECK_SANS_PIED, PUB)
    assert "footer: 'v1.02 du 29.10.26'" in sortie
    assert sortie.split("\n---\n")[0].count("footer:") == 1


@pytest.mark.parametrize("ligne", [
    "footer: 'BTS CIEL-IR · Réseaux'",
    'footer: "BTS CIEL-IR · Réseaux"',
    "footer: BTS CIEL-IR · Réseaux",
])
def test_les_trois_ecritures_du_pied(ligne):
    sortie = preparer_deck(deck_avec_pied(ligne), PUB)
    assert "footer: 'BTS CIEL-IR · Réseaux · v1.02 du 29.10.26'" in sortie
    assert sortie.count("footer:") == 1


def test_apostrophe_du_pied_conservee():
    sortie = preparer_deck(deck_avec_pied('footer: "Cours d\'accueil"'), PUB)
    assert "footer: 'Cours d''accueil · v1.02 du 29.10.26'" in sortie


def test_le_reste_du_deck_est_intact():
    sortie = preparer_deck(DECK, PUB)
    assert "## Le modèle OSI\n\n| Couche | Rôle |\n|---|---|\n| 1 | Physique |" in sortie
    assert sortie.endswith("## Fin\n")
    assert sortie.count("**v1.02**") == 1


def test_la_ligne_est_dans_la_premiere_slide_avant_le_separateur():
    premiere = preparer_deck(DECK, PUB).split("\n---\n")[1]
    assert premiere.rstrip().endswith("**v1.02** — 29 octobre 2026")


def test_un_tiret_triple_dans_un_bloc_de_code_n_est_pas_un_separateur():
    deck = ENTETE.format(pied="footer: 'X'\n") + (
        "\n# Titre\n\n```yaml\n---\nclef: valeur\n---\n```\n\nSuite de la première slide.\n\n---\n\n## Deux\n"
    )
    sortie = preparer_deck(deck, PUB)
    premiere, deuxieme = sortie.split("\n---\n\n## Deux")[0], sortie.split("\n---\n\n## Deux")[1]
    assert "Suite de la première slide.\n\n**v1.02** — 29 octobre 2026" in premiere
    assert "**v1.02**" not in deuxieme
    assert "clef: valeur\n---\n```" in sortie


def test_un_deck_a_une_seule_slide():
    deck = ENTETE.format(pied="footer: 'X'\n") + "\n# Seule\n"
    sortie = preparer_deck(deck, PUB)
    assert sortie.endswith("# Seule\n\n**v1.02** — 29 octobre 2026\n")
    assert "footer: 'X · v1.02 du 29.10.26'" in sortie


def test_le_premier_du_mois_s_ecrit_1er():
    sortie = preparer_deck(DECK, Publication("v2.00", date(2027, 1, 1)))
    assert "**v2.00** — 1er janvier 2027" in sortie


def test_deck_sans_entete_refuse():
    with pytest.raises(ValueError):
        preparer_deck("# Pas d'en-tête\n", PUB)
