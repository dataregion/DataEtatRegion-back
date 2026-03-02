# Instructions Copilot – Backend Data Transform

## 🏗️ Architecture & Vue d’ensemble

- **Backend Python monorepo** pour ETL, import de données et services API.
- **Répertoires principaux** :
  - `app/` : Code principal de l’application (modèles, migrations, services, workers Celery, API).
  - `apis/` : Contexte Docker et configuration des services API.
  - `grist-plugins/` : Plugins et intégrations spécifiques à Grist pour l’export ou la synchronisation de données.
  - `models/`, `services/` : Logique métier, accès aux données, règles de gestion.
  - `migrations/` : Migrations Alembic, avec support multi-base de données (voir ci-dessous).
  - `tests_e2e/`, `app/tests/` : Tests end-to-end et unitaires.
- **Flux de données** : Les données sont ingérées via des workers Celery, traitées, puis exposées via des APIs. Les migrations gèrent l’évolution du schéma et des vues.
- **Pourquoi** : Cette structure permet un ETL robuste multi-base, des migrations reproductibles et un traitement des tâches scalable.

## 🛠️ Workflows critiques

- **Lancer l'API Flask en local (`app/`) [DÉPRÉCIÉ]** :
  1. Se placer dans le dossier `app` :
    ```bash
    cd data-transform/app
    ```
  2. Activer le venv Python :
    ```bash
    source .venv/bin/activate
    ```
  3. Lancer le serveur de développement :
    ```bash
    flask --app app:create_app_api run -h 0.0.0.0
    ```
  4. L'API sera accessible sur http://localhost:8000

- **Lancer les APIs en local (`apis/`)** :
  1. Se placer dans le dossier `apis` :
    ```bash
    cd data-transform/apis
    ```
  2. Activer le venv Python :
    ```bash
    source .venv/bin/activate
    ```
  3. Lancer le serveur de développement :
    ```bash
    uvicorn src.apis.main:app --reload --host 0.0.0.0 --port 8050
    ```
  4. Accéder à la doc interactive : http://localhost:8000/docs

- **Construire les images Docker** : Voir [stack/ansible/templates/data-transform/docker-compose.yml](../stack/ansible/templates/data-transform/docker-compose.yml) et [data-transform/.gitlab-templates/build.gitlab-ci.yml](../data-transform/.gitlab-templates/build.gitlab-ci.yml).
- **Lancer les migrations** : Les migrations Alembic dans `app/migrations/versions/` utilisent un pattern multi-engine (`upgrade_`, `upgrade_audit`, `upgrade_settings`, etc.). Utiliser le bon nom d’engine lors de l’exécution.
  
  **Note (exécution locale) :** Pour éviter des erreurs liées aux shebangs des scripts du venv, lancer `flask`/`alembic` via le Python du venv plutôt que d'exécuter directement les scripts. Par exemple :

  ```bash
  cd data-transform/app
  source .venv/bin/activate
  export FLASK_APP=app:create_app_migrate
  ./.venv/bin/python -m flask db upgrade
  # ou (direct alembic)
  ./.venv/bin/python -m alembic upgrade head
  ```

  Cela évite les erreurs du type "bad interpreter: /path/to/.venv/bin/python3: No such file or directory" lorsque les scripts installés ont un shebang qui n'est pas valide sur la machine.
- **Workers Celery** : Plusieurs files (`line`, `file`, `celery`, etc.) définies dans docker-compose et démarrées avec des paramètres de concurrence/pool différents.
- **Tests** : Tests unitaires dans `app/tests/`, E2E dans `tests_e2e/`. Utiliser pytest pour les tests unitaires.
- **CI/CD** : Les templates GitLab CI dans `.gitlab-templates/` orchestrent builds, déploiements et bump de version.

## 📦 Patterns & conventions spécifiques

- **Migrations** :
  - Chaque fichier de migration définit plusieurs fonctions upgrade/downgrade pour chaque engine DB (ex : `upgrade_`, `upgrade_audit`, etc.).
  - Le boilerplate en fin de fichier dispatch vers la bonne fonction selon l’engine.
  - Utiliser `op.batch_alter_table` pour les changements de schéma sûrs.
  - Les fichiers SQL pour les vues/materialized views sont chargés via des helpers comme `_filecontent`.
- **Celery** :
  - Flower et OCM sont utilisés pour le monitoring et l’orchestration.
- **Config** :
  - Toute la config service est injectée via Docker configs (voir `configs:` dans docker-compose).
  - Les variables d’environnement servent pour les secrets et paramètres dynamiques.
- **Tests** :
  - Les données de test sont sous `tests/data/` et référencées dans les modules de test.
  - Utiliser `pytest` pour les tests Python ; les tests E2E peuvent utiliser d’autres frameworks.
- **API** :
  - Les endpoints API sont définis dans `apis/` et `app/` et exposés via Docker.
  - Toujours passer par les modèles/services pour accéder à la base, jamais de SQL direct dans la logique métier.
- **Routers FastAPI (`apis/`)** :
  - **OBLIGATOIRE : Utiliser l'injection de dépendance pour les sessions de base de données.**
  - **Import des sessions** : `from apis.database import get_session_main, get_session_audit`
  - **Pattern d'injection** : 
    ```python
    def my_endpoint(
        params: QueryParams = Depends(),
        session: Session = Depends(get_session_main),  # ou get_session_audit
        user: ConnectedUser = Depends(keycloak_validator.get_connected_user()),
    ):
    ```
  - **Ne jamais créer manuellement les sessions** : utiliser uniquement les dépendances FastAPI
  - **Session principale** : `get_session_main` pour la base de données principale
  - **Session audit** : `get_session_audit` pour la base de données d'audit
- **Dépréciation des services** :
  - Dans le répertoire `app`, les services sont à déprécier progressivement et doivent être remplacés par des implémentations dans `apis`. Privilégier toute nouvelle logique métier ou refactorisation dans `apis` plutôt que dans `services`.
- **Conventions de codage** :
  - **Fonctions async** : Toute fonction qui retourne une autre fonction asynchrone doit être préfixée par `afn` pour améliorer la lisibilité et faciliter l'identification des fonctions asynchrones.
    - ✅ Correct : `async def afn_fetch_data():`
    - ❌ À éviter : `async def fetch_data():`
- **le paramètre exc_info des méthodes de login** :
  - Le paramètre `exc_info` doit être utilisé pour logger les exceptions avec la stack trace complète, ce qui facilite le debugging. Par exemple :
    ```python
    except Exception as e:
        logger.error("Une erreur est survenue", exc_info=e)
    ```

## 🔗 Intégrations & dépendances externes

- **PostgreSQL** : Base principale, avec plusieurs schémas/engines (main, audit, settings, etc.).
- **Celery** : File de tâches distribuées, avec files custom et monitoring.
- **Docker** : Tous les services tournent en containers ; voir les fichiers compose pour l’orchestration.
- **Grist** : Certains exports de données ciblent Grist (voir références dans le code et compose).
- **Keycloak** : Utilisé pour l’authentification de certains services (voir configs).

## 📚 Fichiers & répertoires clés

- [`app/migrations/versions/`](app/migrations/versions/) : Migrations Alembic, pattern multi-engine.
- [`stack/ansible/templates/data-transform/docker-compose.yml`](../stack/ansible/templates/data-transform/docker-compose.yml) : Orchestration des services.
- [`app/tests/`](app/tests/) : Tests unitaires.
- [`tests_e2e/`](tests_e2e/) : Tests end-to-end.
- [`app/`](app/) : Code principal (modèles, services, celery, API).
- [`app/Dockerfile`](app/Dockerfile) : Build context de l’image principale.

---

**Respecter le pattern multi-base pour les migrations, utiliser les files Celery telles que définies, toujours configurer via Docker/Ansible, et migrer progressivement la logique des services vers `apis`.**

---

*Merci de signaler toute section peu claire ou manquante, et de proposer des améliorations si nécessaire.*
