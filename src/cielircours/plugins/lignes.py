"""Réponses rédigées : `<ins lignes="n">réponse</ins>` devient la réponse (complet) ou n lignes à écrire (trous).

La forme courte `<ins>réponse</ins>` (un trou dans une phrase) est traitée par `trous.py` ;
la forme longue, avec l'attribut `lignes`, occupe un paragraphe à elle seule : la réponse y est
du texte en ligne (gras, code…), sur une ou plusieurs lignes de source.

Le choix de `<ins>` plutôt que d'une syntaxe propre au kit : sur github.com, où `COURS.md` est
lisible, la balise s'affiche comme un trou soulignée, sans rien de visible qui ressemble à du
gabarit (`:::reponse 2`, lui, s'affichait en toutes lettres).

Tout ce qui ressemble à cette forme sans la respecter lève une erreur explicite : un bloc mal
formé laisserait sa réponse en clair dans le document à trous.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from markdown_it import MarkdownIt
from markdown_it.rules_core import StateCore
from markdown_it.token import Token

if TYPE_CHECKING:
    from cielircours.mdtext import Mode

_OUVERTURE = re.compile(r"<ins\s+lignes\s*=\s*\"([^\"]*)\"\s*>\Z", re.IGNORECASE)
_FERMETURE = "</ins>"
_ANCIENNE_SYNTAXE = ":::reponse"
# toute ligne qui commence par l'ancienne syntaxe (casse libre, dans une citation ou une liste aussi)
_ANCIEN_BLOC = re.compile(r"^[ \t>]*:::[ \t]*reponse", re.IGNORECASE | re.MULTILINE)
LIGNES_MAX = 30
_ENTIER = re.compile(r"[0-9]+")


def _html(content: str, level: int) -> Token:
    jeton = Token("html_block", "", 0)
    jeton.content = content
    jeton.block = True
    jeton.level = level
    return jeton


def _nombre_de_lignes(valeur: str) -> int:
    texte = valeur.strip()
    if _ENTIER.fullmatch(texte) is None or int(texte) < 1:
        # échec franc : deviner un nombre laisserait des lignes de la mauvaise taille
        raise ValueError(f'`<ins lignes="n">` attend un nombre de lignes entier positif (chiffres 0-9), reçu {valeur!r}')
    if len(texte) > 4 or int(texte) > LIGNES_MAX:
        raise ValueError(
            f'`<ins lignes="n">` : {valeur!r} lignes, au-delà de la borne de {LIGNES_MAX} '
            "(plus que cela n'est plus une réponse rédigée mais une page blanche)"
        )
    return int(texte)


def _ouverture(jeton: Token) -> re.Match[str] | None:
    if jeton.type != "html_inline":
        return None
    return _OUVERTURE.match(jeton.content.strip())


def _fragment(inline: Token) -> str:
    return inline.content[:80].replace("\n", " ")


def lignes_plugin(md: MarkdownIt, mode: Mode) -> None:
    from cielircours.mdtext import Mode  # import tardif : mdtext importe ce module

    if not isinstance(mode, Mode):
        raise TypeError(f"mode attendu : un Mode, reçu {mode!r}")

    def regle(state: StateCore) -> None:
        ancien = _ANCIEN_BLOC.search(state.src)
        if ancien is not None:
            ligne = state.src[ancien.start() :].splitlines()[0]
            raise ValueError(
                f"la syntaxe `{_ANCIENNE_SYNTAXE} n` n'existe plus : écrire "
                f'`<ins lignes="n">réponse</ins>` dans son propre paragraphe ({ligne.strip()!r})'
            )
        jetons = state.tokens
        i = 0
        while i < len(jetons):
            inline = jetons[i]
            if inline.type != "inline":
                i += 1
                continue
            enfants = inline.children or []
            ouvertures = [k for k, e in enumerate(enfants) if _ouverture(e)]
            if not ouvertures:
                i += 1
                continue

            seul = (
                i > 0
                and jetons[i - 1].type == "paragraph_open"
                and i + 1 < len(jetons)
                and jetons[i + 1].type == "paragraph_close"
                and len(ouvertures) == 1
                and ouvertures[0] == 0
                and enfants[-1].type == "html_inline"
                and enfants[-1].content.lower() == _FERMETURE
            )
            interieur = enfants[1:-1] if seul else []
            if seul and any(e.type == "html_inline" and re.match(r"</?ins\b", e.content, re.IGNORECASE) for e in interieur):
                seul = False  # `<ins>` imbriqué ou fermeture supplémentaire
            if not seul:
                raise ValueError(
                    '`<ins lignes="n">…</ins>` doit occuper un paragraphe à lui seul, bien apparié '
                    f"et sans autre trou à l'intérieur : …{_fragment(inline)}…"
                )

            n = _nombre_de_lignes(_ouverture(enfants[0]).group(1))  # type: ignore[union-attr]
            niveau = jetons[i - 1].level
            if mode is Mode.TROUS:
                jetons[i - 1 : i + 2] = [_html(f'<div class="lignes" style="--n:{n}"></div>\n', niveau)]
            else:
                inline.children = interieur
                jetons[i + 2 : i + 2] = [_html("</div>\n", niveau)]  # après le paragraph_close
                jetons[i - 1 : i - 1] = [_html('<div class="reponse-bloc">\n', niveau)]
                i += 4
            continue

    md.core.ruler.after("inline", "lignes_reponse", regle)
