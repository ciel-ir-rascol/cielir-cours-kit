# TD01 - TD témoin

Ce TD jouet exerce chaque élément de la mise en page d'un TD. Chaque réponse porte un marqueur
que le sujet ne doit jamais montrer.

<div class="ressource" titre="Lire un diagramme">

Une ressource de cours placée **en tête** du TD. Elle peut contenir une liste :

- une classe a trois compartiments ;
- le type s'écrit après le nom.

</div>

## Une partie avec niveau

<p class="partie" duree="20 min" niveau="2"></p>

<div class="dt" titre="Classe Lecteur">

| Attribut | Type | Visibilité |
| --- | --- | :---: |
| `uid` | `string` | `-` |
| `porte` | `Porte` | `-` |

</div>

### Lire le document technique

**Q.** Donner le type de l'attribut `uid` (DT1).

<div class="reponse">

TEMOIN-REPONSE : `string`.

</div>

**Q.** Lister les attributs privés de la classe `Lecteur`, puis écrire leur déclaration C++ :

- en respectant l'ordre du DT1 ;
- avec leur type.

<div class="reponse">

TEMOIN-REPONSE :

- `uid` ;
- `porte`.

```cpp
std::string uid;
Porte porte;
```

</div>

> [!TIP]
> Dans une question « justifier », citez le symbole lu sur le diagramme.

## Une partie sans niveau

<p class="partie" duree="15 min"></p>

<div class="ressource" titre="Multiplicités">

Une ressource placée **en cours de partie**, juste avant les questions qui s'en servent.

</div>

**Q.** Compléter le DR1 : nom de l'association et multiplicité côté `Porte`.

<div class="dr" titre="Association Lecteur – Porte">

![Association à compléter](img/dr-exemple.svg)

</div>
