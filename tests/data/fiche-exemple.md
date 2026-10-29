## Pourquoi apprendre le C++ ?

Le C++ est un langage <ins>rapide</ins>, <ins>flexible</ins> et <ins>portable</ins>. Il permet deux paradigmes de programmation : <ins>procédural</ins> et <ins>orienté objet</ins>.

Son principal inconvénient : <ins>sa complexité, qui impose de la rigueur</ins>.

## Historique

| Date | Événement | Date | Événement |
| --- | --- | --- | --- |
| **1979** | <ins>Bjarne Stroustrup</ins> crée « C with Classes » | **1998 / 2003** | Standards <ins>C++98</ins> et <ins>C++03</ins> |
| **1983** | Le langage est rebaptisé <ins>C++</ins> | **2011** | Début du C++ moderne (C++11, 14, 17, 20, 23) |

## Processus de construction du programme

*Compléter les mots qui manquent dans le texte.*

Le code source est écrit dans un langage de <ins>haut</ins> niveau, pensé pour les <ins>humains</ins>. Le code objet est un code de <ins>bas</ins> niveau, destiné à <ins>la machine</ins>. Le **linker** <ins>assemble</ins> le code objet avec les <ins>bibliothèques</ins> utilisées et crée le programme.

> [!NOTE]
> Un fichier d'en-tête déclare ce qu'une bibliothèque offre ; il ne contient pas son code.

## Structure d'un programme C++

```cpp
#include <iostream>
using namespace std;

int main() {
    int nbFavori;
    cout << "Entrez votre nombre favori : ";
    cin >> nbFavori;
    cout << "Super ! C'est aussi le mien !" << endl;
    return 0;
}
```

Si l'utilisateur saisit 42, le programme affiche :

:::reponse 2
```text
Entrez votre nombre favori : 42
Super ! C'est aussi le mien !
```
:::

> [!TIP]
> Compiler avec `g++ -Wall -Wextra` révèle déjà la moitié des erreurs d'étourderie.

## Les directives de préprocesseur

Le préprocesseur traite le code <ins>avant</ins> le compilateur. Il supprime les <ins>commentaires</ins> et traite les lignes commençant par <ins>#</ins>. Inclure une bibliothèque standard : <ins>#include</ins> `<iostream>`. Définir une constante : <ins>#define</ins> `PinMoteur 22`.

> [!IMPORTANT]
> Une directive ne se termine pas par un point-virgule.

## Les flux d'entrée et de sortie

| Objet | Flux | Rôle | Opérateur |
| --- | --- | --- | --- |
| `cout` | <ins>sortie</ins> | <ins>afficher à l'écran</ins> | `<<` |
| `cin` | <ins>entrée</ins> | <ins>lire au clavier</ins> | `>>` |

Le type de la valeur saisie doit correspondre au <ins>type</ins> de la variable qui la reçoit.

> [!WARNING]
> `cin` laisse le retour à la ligne dans le tampon : la lecture suivante peut échouer.

*Écrire les instructions qui affichent « Quel âge as-tu ? » puis lisent la saisie dans `age` :*

:::reponse 3
```cpp
cout << "Quel âge as-tu ? ";
cin >> age;
```
:::

> [!CAUTION]
> Un `int` non initialisé contient une valeur quelconque : ne jamais le lire avant de l'avoir écrit.
