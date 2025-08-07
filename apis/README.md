# Pour le développement

## [Concepts de base](./../.markdowns/installation_venv_for_application.md)

## Executer les tests

```bash
pytest # execute les tests unitaires
pytest -m integration # execute les tests d'intégration
```

## Mettre à jour les dépendances

```bash
rm requirements.external.txt
pip-compile requirements.external.in \
  ../models/pyproject.toml \
  ../services/pyproject.toml \
  ../gristcli/pyproject.toml \
  -o requirements.external.txt
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
