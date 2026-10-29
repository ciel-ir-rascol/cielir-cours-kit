# Verdict : visibilité du kit `cielir-cours-kit`

Date : 2026-10-29

## Question

Un dépôt **public** peut-il consommer (`uses:`) une action composite hébergée dans un dépôt
**internal** de la même organisation (`ciel-ir-rascol`, plan enterprise) ?

Les dépôts de cours sont publics (les étudiants les consultent) ; le kit était prévu en internal.

## Protocole

1. Kit créé en internal, branches `main` et `construction-kit` poussées :
   `gh repo create ciel-ir-rascol/cielir-cours-kit --internal --source=. --remote=origin`
2. `action.yml` minimal à la racine du kit, sur la branche `construction-kit` (action composite,
   une seule étape `run: echo ok`, `shell: bash`).
3. Dépôt jetable **public** `ciel-ir-rascol/essai-action-internal`, dont le workflow
   `essai.yml` (déclencheur `workflow_dispatch`) contient :
   ```yaml
   steps:
     - uses: ciel-ir-rascol/cielir-cours-kit@construction-kit
   ```
   (une référence de branche se résout comme `@main` ; `main` est resté propre.)

## Commande lancée

```bash
gh workflow run essai.yml --repo ciel-ir-rascol/essai-action-internal
```

## Sortie observée

Le job échoue dès l'étape « Set up job » (2 s), avant tout téléchargement de l'action :

```
##[error]Unable to resolve action `ciel-ir-rascol/cielir-cours-kit`, not found
```

Résumé : `X main essai · 40909311530` (échec, workflow_dispatch).

## Décision

**Non : un dépôt public ne peut pas utiliser une action hébergée dans un dépôt internal.**
Le kit est donc passé en **public** :

```bash
gh repo edit ciel-ir-rascol/cielir-cours-kit --visibility public --accept-visibility-change-consequences
```

**Visibilité retenue pour `ciel-ir-rascol/cielir-cours-kit` : public.**

Aucun contournement par jeton n'a été tenté : la règle posée était « internal, sinon public ».
Conséquence : le contenu du kit est lisible par tous, d'où l'interdiction d'y mettre toute
information personnelle enseignante ou tout secret.

Le dépôt d'essai a été supprimé.
