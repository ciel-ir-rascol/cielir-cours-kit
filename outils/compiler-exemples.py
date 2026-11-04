"""Les exemples de code d'un cours doivent compiler, et afficher ce que le cours annonce.

Depuis la racine du kit :

    uv run python outils/compiler-exemples.py <dépôt>

Le script lit `COURS.md` et `slides/*.md`, en extrait chaque bloc ```cpp, le compile — dans un
`main` minimal, ou tel quel s'il porte déjà le sien — et, quand le bloc annonce une sortie
console, l'exécute pour comparer.

Il ne demande rien d'autre que `g++`. Les trous du kit (`<ins>…</ins>`) sont retirés avant
compilation : c'est la réponse qui est compilée, puisque c'est elle que l'étudiant doit écrire.

**Pourquoi cet outil existe.** Sur `cpp-c06`, il a trouvé en une passe quatre défauts qu'aucune
relecture n'avait vus : un exemple qui ne compilait pas du tout (quatre erreurs, dont un
`cout >>` au lieu de `cout <<`), un tableau déclaré `[4][4]` mais initialisé en 3 × 3 dont la
sortie annoncée était fausse, une boucle sur un littéral de chaîne qui fait un tour de plus que
le cours ne le dit, et un test de bornes qui refusait les valeurs qu'il prétendait accepter.
Un cours de programmation se relit mal : il se compile.

**Pourquoi il ne signale pas tout ce qui ne compile pas.** Un cours ne contient pas que des
programmes : il montre des squelettes (`while (condition)`), des expressions seules
(`age == 18   // true`), des mémos de syntaxe. Compilés hors de leur contexte, tous échouent
sans que rien ne soit faux. Le script ne retient donc que les erreurs qu'un contexte manquant
ne peut pas produire — un opérateur qui n'existe pas pour ces types, une accolade là où le
langage attend une expression. La liste est courte à dessein : un outil qui crie au loup ne
sert plus à rien. Il rate donc des fautes, et c'est assumé ; la comparaison des sorties, elle,
ne rate rien de ce qu'un bloc annonce.

**Ce qu'il ne peut pas voir.** Un programme qui compile et tourne peut enseigner une bêtise :
le script juge le code, pas la pédagogie. Il ne vérifie une sortie que si le bloc l'annonce, et
il ne sait pas alimenter un programme qui lit l'entrée standard — un exemple à base de `cin`
est compilé, jamais exécuté.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ENTETE = """#include <iostream>
#include <vector>
#include <string>
using namespace std;
"""

_BLOC = re.compile(r"```cpp\n(.*?)```", re.DOTALL)
_INS = re.compile(r"</?ins(?:\s+lignes=\"\d+\")?>")
# la sortie annoncée, telle que les cours l'écrivent : /* 🖥️ SORTIE CONSOLE … */
_SORTIE = re.compile(r"/\*[^\n]*SORTIE CONSOLE\n(.*?)\*/", re.DOTALL)
_LIT_ENTREE = re.compile(r"\bcin\s*>>")
# un bloc qui porte déjà son main est un programme entier : on le compile tel quel
_PROGRAMME = re.compile(r"^\s*(int|void)\s+main\s*\(", re.MULTILINE)
# une erreur qui ne dit que « cet identifiant n'existe pas » trahit un squelette, pas une faute
# Un cours ne contient pas que des programmes : il montre des squelettes (`while (condition)`),
# des expressions seules (`age == 18   // true`), des mémos de syntaxe. Compilés hors contexte,
# tous échouent sans que rien ne soit faux. On ne retient donc que les erreurs qu'un contexte
# manquant ne peut pas produire — liste volontairement courte, pour ne jamais crier au loup.
_FRANCHES = (
    re.compile(r"no match for ‘operator"),          # cout >> au lieu de cout <<
    re.compile(r"expected primary-expression before ‘\{’"),  # accolades autour d'une expression
    re.compile(r"invalid operands of types"),
    re.compile(r"cannot convert ‘[^’]+’ to ‘[^’]+’ in (initialization|assignment)"),
)


def _blocs(depot: Path) -> list[tuple[str, int, str]]:
    fichiers = [depot / "COURS.md", *sorted((depot / "slides").glob("[0-9][0-9]-*.md"))]
    trouves = []
    for f in fichiers:
        if not f.is_file():
            continue
        for n, bloc in enumerate(_BLOC.findall(f.read_text(encoding="utf-8")), 1):
            trouves.append((f.name, n, _INS.sub("", bloc)))
    return trouves


def _compiler(code: str, dossier: Path, nom: str, executer: bool) -> tuple[int, str, str]:
    """Rend (code de retour, erreurs de compilation, sortie du programme).

    La compilation est silencieuse (`-w`) : un avertissement n'est pas une faute de cours.
    """
    source = dossier / f"{nom}.cpp"
    entier = _PROGRAMME.search(code)
    texte = code if entier else ENTETE + "int main() {\n" + code + "\nreturn 0;\n}\n"
    if entier and "#include" not in code:
        texte = ENTETE + code
    source.write_text(texte, encoding="utf-8")
    binaire = dossier / nom
    args = ["g++", "-std=c++17", "-w"]
    args += ["-o", str(binaire)] if executer else ["-fsyntax-only"]
    r = subprocess.run([*args, str(source)], capture_output=True, text=True)
    if r.returncode or not executer:
        return r.returncode, r.stderr, ""
    try:
        e = subprocess.run([str(binaire)], capture_output=True, text=True,
                           stdin=subprocess.DEVNULL, timeout=5)
        return 0, "", e.stdout
    except subprocess.TimeoutExpired:
        return 0, "", "<<le programme ne s'est pas arrêté en 5 s>>"


def _normaliser(texte: str) -> list[str]:
    return [l.strip() for l in texte.strip().splitlines() if l.strip()]


def controler(depot: Path) -> int:
    blocs = _blocs(depot)
    fragments, fautes, sorties_fausses, verifies = 0, [], [], 0

    with tempfile.TemporaryDirectory() as tmp:
        dossier = Path(tmp)
        for i, (fichier, n, code) in enumerate(blocs):
            attendue = _SORTIE.search(code)
            executable = bool(attendue) and not _LIT_ENTREE.search(code)
            retour, erreurs, sortie = _compiler(code, dossier, f"b{i}", executable)

            if retour:
                lignes = [l for l in erreurs.splitlines() if ": error:" in l]
                franche = next((l for l in lignes
                                if any(m.search(l) for m in _FRANCHES)), None)
                if franche is None:
                    fragments += 1
                else:
                    debut = code.strip().splitlines()[0][:58]
                    fautes.append((fichier, n, debut, franche.split("error:")[-1].strip()[:80]))
                continue

            if executable:
                verifies += 1
                obtenue, voulue = _normaliser(sortie), _normaliser(attendue.group(1))
                if obtenue != voulue:
                    sorties_fausses.append((fichier, n, voulue, obtenue))

    print(f"{depot.name} : {len(blocs)} blocs C++, dont {fragments} squelettes de syntaxe")
    print(f"  ne compilent pas  : {len(fautes)}")
    for fichier, n, debut, erreur in fautes:
        print(f"    {fichier} bloc {n} — « {debut} »")
        print(f"       {erreur}")
    print(f"  sorties vérifiées : {verifies}, dont {len(sorties_fausses)} fausses")
    for fichier, n, voulue, obtenue in sorties_fausses:
        print(f"    {fichier} bloc {n}")
        print(f"       annoncé : {' / '.join(voulue)[:70]}")
        print(f"       obtenu  : {' / '.join(obtenue)[:70]}")

    return 1 if fautes or sorties_fausses else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("depot", type=Path, help="le dépôt de cours (celui de COURS.md)")
    args = parser.parse_args()
    if not (args.depot / "COURS.md").is_file():
        print(f"{args.depot} ne contient pas de COURS.md", file=sys.stderr)
        return 2
    return controler(args.depot)


if __name__ == "__main__":
    sys.exit(main())
