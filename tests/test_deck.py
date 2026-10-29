from datetime import date
from pathlib import Path

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


def _deck_une_slide(contenu):
    """Deck dont la première slide est `contenu`, suivie d'une seconde slide."""
    return ENTETE.format(pied="footer: 'X'\n") + "\n" + contenu + "\n\n---\n\n## Deux\n"


def _dans_la_premiere_slide(sortie):
    """Vrai si l'unique ligne de version précède la seconde slide (repérée par son titre)."""
    suivante = "## Suite" if "## Suite" in sortie else "## Deux"
    return sortie.count("**v1.02** —") == 1 and sortie.index("**v1.02** —") < sortie.index(suivante)


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
def test_la_version_va_toujours_dans_la_premiere_slide(contenu):
    sortie = preparer_deck(_deck_une_slide(contenu), PUB)
    assert _dans_la_premiere_slide(sortie)


def test_la_version_n_est_pas_dans_un_commentaire():
    deck = _deck_une_slide("# T\n\n<!--\nNote\n\n---\n\nsuite\n-->")
    sortie = preparer_deck(deck, PUB)
    assert sortie.index("**v1.02** —") > sortie.index("-->")


def test_un_titre_setext_n_est_pas_un_separateur():
    deck = _deck_une_slide("Titre\n---\n\nSuite du texte")
    sortie = preparer_deck(deck, PUB)
    assert "Suite du texte\n\n**v1.02**" in sortie
    assert _dans_la_premiere_slide(sortie)


def test_entete_non_referme_refuse():
    with pytest.raises(ValueError):
        preparer_deck("---\nmarp: true\n\n# Titre\n", PUB)


def test_le_vrai_deck_git_cours01():
    chemin = (Path(__file__).resolve().parents[2]
              / "git-cours01-decouverte/slides/01-decouverte-git-github.md")
    if not chemin.exists():
        pytest.skip("dépôt git-cours01-decouverte absent")
    source = chemin.read_text(encoding="utf-8")
    sortie = preparer_deck(source, PUB)
    assert "footer: 'BTS CIEL-IR · Git et GitHub · 1re année · v1.02 du 29.10.26'" in sortie
    assert sortie.count("**v1.02** — 29 octobre 2026") == 1
    notes = sortie.index("Commencer par un tour de table")
    assert notes < sortie.index("**v1.02**") < sortie.index("## Vous avez déjà vu ça ?")
    ajoutees = [l for l in sortie.splitlines() if l not in source.splitlines()]
    assert len(ajoutees) == 2
