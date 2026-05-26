# APIs

| Variable d'environnement | Description                        |
| ------------------------ | ---------------------------------- |
| APIS_CONFIG_PATH         | Chemin du fichier de configuration |

# Pour le développement

## Lancer les APIs en mode développement

Pour démarrer les APIs en mode développement (hot reload, logs détaillés), assurez-vous d'abord d'avoir installé les dépendances :


## [Installation du venv](./../.markdowns/installation_venv_for_application.md)


Puis lancez le serveur avec :


```bash
source .venv/bin/activate && uvicorn src.apis.main:app --reload --host 0.0.0.0 --port 8050
```

Vous pouvez ensuite accéder à la documentation interactive sur http://localhost:8050/docs

## Conventions

- **Sessions DB** : utiliser obligatoirement l'injection FastAPI `Depends(get_session_main)` ou `Depends(get_session_audit)` (depuis `apis.database`). Ne jamais instancier de session manuellement.
- **Préfixe `afn_`** pour toute fonction `async def` qui retourne une coroutine.
- **Logs d'exception** : `logger.error("msg", exc_info=e)` pour conserver la stack trace.
- **Accès données** : toujours via `models/` + `services/`, jamais de SQL inline.

Voir `CLAUDE.md` à la racine pour la liste complète et `/check-backend apis` pour le lint local.

> **Note** : Adaptez le chemin du module (`src.apis.main:app`) si la structure change.

## Executer les tests

```bash
pytest # execute les tests unitaires
pytest -m integration # execute les tests d'intégration
```

## Mettre à jour les dépendances

```bash
rm requirements.external.txt # à supprimer pour des montées des version plus aggressives
./.build-helper-scripts/update-requirements-external.sh
```

## Requêter les apis externes telles que configuré dans le projet

```bash
cli data_subventions_client --help
# 
cli data_subventions_client subventions 33284688000018
```

## Rafraichir les schemas pour autocompletion

A utiliser avec l'extension officielle de redhat pour la lecture du yaml: https://github.com/redhat-developer/vscode-yaml

```bash
cli refresh-dev-schemas
```

## Pre commit hooks

Il est possible d'installer des pre-commit hook prédéfinis (grâce à [https://pre-commit.com/](https://pre-commit.com/)).
Ils sont configurés ici: [.pre-commit-config.yaml](./.pre-commit-config.yaml)

Après l'installation du venv et des dépendances de dev, executer:

```bash
pre-commit install
```

activera les pre-commit hooks
