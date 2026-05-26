# Data Transform — Backend monorepo

## Stack
- Python 3.12.6, uv
- **apis/** (cible) : FastAPI 0.115.5 + SQLAlchemy
- **batches/** : Prefect
- **grist-plugins/** : FastAPI + Jinja2 (widgets Grist)
- **app/** : Flask + Flask-RESTx + Celery — **DÉPRÉCIÉ**, transposer vers `apis/`
- Libs : `models/`, `services/`, `gristcli/`, `supersetcli/`
- Infra : PostgreSQL multi-engine (main/audit/settings), Alembic, Celery, Keycloak, Docker

## Commandes
```bash
# apis (8050)
cd apis && source .venv/bin/activate && uvicorn src.apis.main:app --reload --host 0.0.0.0 --port 8050

# grist-plugins (8051)
cd grist-plugins && source .venv/bin/activate && uvicorn src.grist_plugins.main:app --reload --host 0.0.0.0

# app legacy (5000)
cd app && flask --app app:create_app_api run -h 0.0.0.0

# Alembic (utiliser python -m, shebang venv cassé)
cd app && export FLASK_APP=app:create_app_migrate && ./.venv/bin/python -m flask db upgrade

# Tests
pytest                  # unit
pytest -m integration   # E2E

# Deps épinglées
rm requirements.external.txt && ./.build-helper-scripts/update-requirements-external.sh

# Lint miroir CI
/check-backend
```

## Conventions
- **Sessions FastAPI** : `Depends(get_session_main)` ou `Depends(get_session_audit)` depuis `apis.database`. Jamais manuel.
- **Préfixe `afn_`** pour `async def` retournant une coroutine.
- **Logs** : `logger.error("msg", exc_info=e)`.
- **Alembic multi-engine** : `upgrade_<engine>`/`downgrade_<engine>` (`_`, `audit`, `settings`), `op.batch_alter_table` pour DDL.
- **DB** : via `models/` + `services/`. Pas de SQL inline.
- Nouvelles features → `apis/`.

## À éviter
- Session DB sans `Depends(...)`.
- Code neuf dans `app/services`.
- SQL brut dans contrôleurs.
- `./.venv/bin/flask` direct (shebang KO) → `python -m flask`.
- Bypass `models/`.

## Réfs
-`.gitlab-templates/`, `README.md` (flux data)
