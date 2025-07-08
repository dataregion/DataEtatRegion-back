# Pour le développement

## [Concepts de base](./../.markdowns/installation_venv_for_application.md)

## Mettre à jour les dépendances

```bash
rm requirements.external.txt
pip-compile requirements.external.in \
  ../models/pyproject.toml \
  ../services/pyproject.toml \
  ../gristcli/pyproject.toml \
  -o requirements.external.txt
```

## Pre commit hooks

Il est possible d'installer des pre-commit hook prédéfinis (grâce à [https://pre-commit.com/](https://pre-commit.com/)).
Ils sont configurés ici: [.pre-commit-config.yaml](./.pre-commit-config.yaml)

Après l'installation du venv et des dépendances de dev, executer:

```bash
pre-commit install
```

activera les pre-commit hooks

## Comment initialiser un script de migration de base

En utilisant flask db migrate. Voici la commande:

```
env FLASK_APP=app:create_app_migrate flask db migrate -m "Message plus long" --rev-id "20231026_cequefaitlescript"
```

En savoir plus sur [la migration de database](./README-dbmigration.md) pour le développeur.

## Mode Api

```bash
$ FLASK_APP="app:create_app_api" flask run  --host "0.0.0.0"
```

## Tests unitaires

Utilisent pytest.

### Faker

La lib faker est utilisé pour certains tests. Afin qu'ils soient reproductibles il est possible de passer un seed au tests via:

`pytest -seed 1234`

Aussi, lors de leur execution, le seed utilisé est affiché.


# Utilisation

## UserManagement

Pour utiliser ces API, vous pouvez utiliser un outil de test d'API comme Postman ou Insomnia. Voici les différentes routes disponibles :

* `GET /users` : Récupère la liste de tous les utilisateurs avec des informations de pagination
PATCH /users/disable/<uuid> : Désactive un utilisateur avec l'ID spécifié
* `PATCH /users/disable/<uuid>` : Désactive un utilisateur avec l'ID spécifié
* * `PATCH /users/enable/<uuid>` : Active un utilisateur avec l'ID spécifié

