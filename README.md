<h1 align="center" style="border-bottom: none">
    <div>
        API Regate Num Data Etat
    </div>
</h1>

<p align="center">
    Gestion des API pour le projet Regate Num Data Etat<br/>
</p>

<div align="center">
 
[![Conventional Commits](https://img.shields.io/badge/Conventional%20Commits-1.0.0-green.svg)](https://conventionalcommits.org)
[![Python version](https://img.shields.io/badge/python-3.12.1-blue)](https://www.python.org/downloads/release/python-3121/)
[![Flask version](https://img.shields.io/badge/Flask-2.1.3-blue)](https://flask.palletsprojects.com/en/2.1.x/)
[![Postgresql version](https://img.shields.io/badge/Postgresql-informational)](https://www.postgresql.org/)
[![Docker build](https://img.shields.io/badge/docker-automated-informational)](https://docs.docker.com/compose/)

</div>


# Description

Ce projet contient une suite d'API REST développées avec Flask-RESTx et Python 3.12. 
Ces API permettent de gérer des utilisateurs Keycloak, en les activant ou en les désactivant. 
Elles permettent également d'intégrer les fichiers Chorus de l'état pour recouper les données.

# Pour le développement

## Fichiers de configuration

Copier le fichier [config_template.yml](./config/config_template.yml) en config.yml.
```
cp config/config_template.yml config/config.yml
```

Copier le fichier [oidc_template.yml](./config/oidc_template.yml) en config.yml.
```
cp config/oidc_template.yml config/oidc.yml
```


## Installation

*Initialisez un venv python*. Puis:

```bash
pip install pip-tools
# Pour mettre à jour les dépendances épinglées
pip-compile --resolver=backtracking && pip-compile --resolver=backtracking dev-requirements.in
pip install -r requirements.txt -r dev-requirements.txt
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

