# Verdict : visibilité du kit `cielir-cours-kit`

Date : 2026-10-29

## Question

Un dépôt **public** peut-il consommer (`uses:`) une action composite hébergée dans un dépôt
**internal** de la même organisation (`ciel-ir-rascol`, plan enterprise) ?

Les dépôts de cours sont publics (les étudiants les consultent) ; le kit était prévu en internal.

## Protocole

1. Kit créé en internal, branches `main` et `construction-kit` poussées :
   `gh repo create ciel-ir-rascol/cielir-cours-kit --internal --source=. --remote=origin`
   puis `git push origin main construction-kit`.
2. `action.yml` minimal à la racine du kit, sur la branche `construction-kit` (action composite,
   une seule étape `run: echo ok`, `shell: bash`).
3. Dépôt jetable **public** `ciel-ir-rascol/essai-action-internal`, dont le workflow
   `essai.yml` (déclencheur `workflow_dispatch`) contient :
   ```yaml
   steps:
     - uses: ciel-ir-rascol/cielir-cours-kit@construction-kit
   ```

**Écart au plan, à lire comme une hypothèse.** Le plan prévoyait `@main` ; l'essai a visé
`@construction-kit` (la branche qui portait l'`action.yml`), pour garder `main` propre.
On suppose qu'une référence de branche se résout comme une autre ; **ce n'est pas démontré** et
l'essai n'a pas été refait avec `@main`. Le dépôt étant depuis passé en public, refaire l'essai
exigerait de le rebasculer en internal.

## Commandes lancées et sorties

Déclenchement :

```bash
gh workflow run essai.yml --repo ciel-ir-rascol/essai-action-internal
```

Lecture (après `sleep 15`, `gh run watch` n'a pas été utilisé) :

```bash
gh run list --repo ciel-ir-rascol/essai-action-internal
gh run view 40909311530 --repo ciel-ir-rascol/essai-action-internal --log | head -40
gh run view 40909311530 --repo ciel-ir-rascol/essai-action-internal
```

Extraits, avec la commande qui les a produits :

- `gh run list` : `completed	failure	essai	essai	main	workflow_dispatch	40909311530	9s	2026-10-29T16:12:44Z`
- `gh run view … --log | head -40` (ligne d'erreur, reproduite telle que sortie, préfixe
  job/étape et horodatage compris) :
  ```
  essai	Set up job	2026-10-29T16:12:50.9914013Z ##[error]Unable to resolve action `ciel-ir-rascol/cielir-cours-kit`, not found
  ```
  Juste avant : « Prepare all required actions », « Getting action download info ». Le job
  échoue à l'étape « Set up job », avant toute exécution.
- `gh run view …` (sans `--log`) : `X main essai · 40909311530`, `X essai in 2s`, annotation
  `X Unable to resolve action `ciel-ir-rascol/cielir-cours-kit`, not found`.

Le message de GitHub ne mentionne pas la référence (`@construction-kit`) : cette absence est
dans la sortie d'origine, ce n'est pas une troncature de ce document.

**Journal non conservé.** Le dépôt d'essai a été supprimé ; le run et son journal ne sont plus
récupérables (`gh run view 40909311530` répond maintenant HTTP 404). Les extraits ci-dessus ont été
copiés de la sortie du terminal au moment de l'essai, pas reconstitués ; seule la sortie de
`gh run view --log` est limitée à ses 40 premières lignes (`head -40`), le reste du journal n'a
pas été lu.

## Limites de l'observation

- **Pas de témoin.** Seul le cas « public vers internal » a été essayé. On n'a pas vérifié qu'un
  dépôt internal (ou privé) de l'organisation résout la même action, ni testé la même action une fois
  le kit public.
- **Réglage « Actions > Accès » non relevé.** Pour un dépôt internal, ce réglage (« Accessible
  from repositories in the organization ») est désactivé par défaut. Il n'a pas été relevé avant
  l'essai et ne peut plus l'être : l'API répond désormais
  `422 Access policy only applies to internal and private repositories` car le kit est public. On
  suppose donc, sans l'avoir vu, qu'il était à sa valeur par défaut.
  Le message « not found » ne distingue pas à lui seul « dépôt public interdit » de « accès
  non activé ».
- Résultat valable en configuration par défaut, un seul essai.

## Ce que dit la documentation GitHub

Page « Sharing actions and workflows with your enterprise »
(https://docs.github.com/en/actions/how-tos/reuse-automations/share-with-your-enterprise ;
source : `content/actions/how-tos/reuse-automations/share-with-your-enterprise.md` du dépôt
`github/docs`, lue le 2026-10-29) :

> Actions and reusable workflows stored in internal repositories cannot be used in public
> repositories and actions and reusable workflows stored in private repositories cannot be used
> in public or internal repositories.

Cela tranche la question indépendamment du réglage « Accès » : celui-ci n'ouvre l'accès qu'à des
dépôts internal ou privés. Il confirme donc l'échec observé et écarte l'hypothèse « il suffisait
d'activer l'accès ».

## Décision

Un dépôt public ne peut pas utiliser une action hébergée dans un dépôt internal : **constaté en
configuration par défaut, sans témoin, et conforme à la documentation GitHub citée ci-dessus.**
Le kit est donc passé en **public** :

```bash
gh repo edit ciel-ir-rascol/cielir-cours-kit --visibility public --accept-visibility-change-consequences
```

**Visibilité retenue pour `ciel-ir-rascol/cielir-cours-kit` : public.**

Aucun contournement par jeton n'a été tenté : la règle posée était « internal, sinon public ».
Conséquence : le contenu du kit est lisible par tous, d'où l'interdiction d'y mettre toute
information personnelle enseignante ou tout secret.

Le dépôt d'essai a été supprimé.
