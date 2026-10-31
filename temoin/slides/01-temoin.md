---
marp: true
theme: ciel
paginate: true
lang: fr
title: Du code source au programme
description: Deck du dépôt témoin du kit, qui reprend le plan et le schéma du cours.
header: 'Du code source au programme'
footer: 'Informatique · Témoin du kit · 1CIELIR'
---

<!-- _class: lead -->
<!-- _paginate: false -->
<!-- _header: '' -->
<!-- _footer: '' -->

# C01 - Du code source au programme

## Informatique - Témoin du kit

1CIELIR - Lycée Louis Rascol, Albi

<!--
Ce deck est le pendant du COURS.md du témoin : même plan, même schéma (le même fichier).
-->

---

## Pourquoi apprendre le C++ ?

- Un langage **rapide**, **flexible** et **portable**
- Deux paradigmes : procédural et orienté objet
- Son prix : de la **rigueur**

| Date | Événement |
| --- | --- |
| 1979 | « C with Classes » |
| 1983 | Rebaptisé C++ |
| 2011 | Début du C++ moderne |

---

## Du code source au programme

<img class="schema" src="img/schema.svg" alt="Chaîne de construction : code source, compilation, code objet, édition de liens, programme">

---

## Premier programme

```cpp
#include <iostream>
using namespace std;

int main() {
    int age;
    cout << "Quel âge as-tu ? ";
    cin >> age;
    cout << "Tu as " << age << " ans." << endl;
    return 0;
}
```

> Une directive de préprocesseur ne se termine pas par un point-virgule.

---

<!-- _class: piege -->

## Compiler et exécuter

```text
$ g++ -Wall -o age age.cpp
$ ./age
Quel âge as-tu ? 17
Tu as 17 ans.
```

> `cin` laisse le retour à la ligne dans le tampon : une lecture de texte qui suit peut échouer.

---

## Crédits

| Élément | Auteur | Licence |
| --- | --- | --- |
| Schéma de la chaîne de construction | Création originale du kit | CC BY-NC-SA 4.0 |

Ce document est publié sous licence CC BY-NC-SA 4.0.
