# Les migrations de base de données

Les migrations sont décrites dans le dossier [migrations/versions](./migrations/versions/).

Le module [flask-migrate](https://flask-migrate.readthedocs.io/en/latest/) est utilisé. 

## Passage de configuration single db vers multi db

Début mars 2024, nous sommes passés du mode `single-db` au mode `multi-db` de flask-migrate.

C'est une modification qui implique de repartir d'un dossier [migrations](./migrations/) vide, aussi, les « anciennes » migrations sont maintenant localisées dans le dossier [migrations.old](./migrations.old/).

### Downgrade vers des versions antérieures à début mars 2024

La modification décrite ci-dessus « casse » la chaine de downgrade / upgrade. Il est toujours possible de revenir à une version antérieure à ladite modification de cette manière.

- downgrade jusqu'à la première version des migrations post mars 2024

```bash
env FLASK_APP=app:create_app_migrate flask db downgrade "20240304_indices_for_ae_deletion"
```

*Les anciennes et nouvelles migrations ont toutes deux une revision nommée `20240304_indices_for_ae_deletion`. Ce qui permet de faire la transition entre les deux configurations.*

- Faire pointer Flask-Migrate vers l'ancien dossier de migrations en éditant [app/__init__.py](./app/__init__.py)

```python
...

def create_app_migrate():
    import app.models

    app = create_app_base(oidc_enable=False, expose_endpoint=False)
    #migrate = Migrate() # XXX: On pointe vers les anciennes migrations
    migrate = Migrate(directory="migrations.old")

    migrate.init_app(app, db)
    return app

...
```

A partir de là, utiliser les commandes de migration classiques.