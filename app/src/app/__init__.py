# __init__.py is a special Python file that allows a directory to become
# a Python package so it can be accessed using the 'import' statement.
import logging

import yaml
from app.utilities import sqlalchemy_pretty_printer
from flask import Flask
from flask_caching import Cache
from flask_marshmallow import Marshmallow
from flask_migrate import Migrate
from prometheus_flask_exporter import PrometheusMetrics
from werkzeug.middleware.proxy_fix import ProxyFix

from app import celeryapp, mailapp

from flask_cors import CORS

from app.database import db
from app.auth import KeycloakIntrospectTokenValidator, auth


# TODO déplacer en extensions
ma = Marshmallow()
cache = Cache()
prometheus = PrometheusMetrics.for_app_factory(group_by="endpoint")


def create_app_migrate():
    import app.models

    app = create_app_base(oidc_enable=False, expose_endpoint=False)
    migrate = Migrate()

    migrate.init_app(app, db)
    return app


def create_app_api():
    api_app = create_app_base()

    if api_app.config.get("ENABLE_API_METRICS", False):
        logging.info("Setting up prometheus metrics.")
        prometheus.init_app(api_app)
    else:
        logging.warning("Metrics are disabled ! use `ENABLE_API_METRICS` feature flag to enable it.")

    return api_app


def create_app_base(
    oidc_enable=True,
    expose_endpoint=True,
    init_celery=True,
    config_filep="config/config.yml",
    oidc_config_filep="config/oidc.yml",
    extra_config_settings=None,
    **kwargs,
) -> Flask:
    """Create a Flask application."""

    if extra_config_settings is None:
        extra_config_settings = {}

    _format = "%(asctime)s.%(msecs)03d : %(levelname)s : %(message)s"
    logging.basicConfig(format=_format, datefmt="%Y-%m-%d %H:%M:%S", level=logging.INFO, force=True)

    sqlalchemy_pretty_printer.setup(format=_format)

    # Instantiate Flask
    app = Flask(__name__)
    read_config(app, config_filep, extra_config_settings)
    db.init_app(app)
    ma.init_app(app)

    # Celery
    if init_celery:
        celery = celeryapp.create_celery_app(app)
        celeryapp.celery = celery

        mail = mailapp.create_mail_app(app)
        mailapp.mail = mail

    # init oidc
    if oidc_enable:
        try:
            _load_oidc_config(app, oidc_config_filep)
        except Exception:
            logging.exception("Impossible de charger la configuration OIDC. Merci de vérifier votre configuration.")
            raise

    # TODO, à terme mettre un cache REDIS ou autre, utilisable pour les autres apis
    # Utiliser uniquement pour Demarche simplifie pour un POC
    cache.init_app(app, config={"CACHE_TYPE": "SimpleCache", "CACHE_DEFAULT_TIMEOUT": 300})

    # flask_restx
    app.config.update({"RESTX_INCLUDE_ALL_MODELS": True})
    if expose_endpoint:
        app.config.SWAGGER_UI_OAUTH_CLIENT_ID = app.config.get("KEYCLOAK_OPENID", {}).get("CLIENT_ID", None)
        _expose_endpoint(app)

    _post_create_app_base(app)
    return app


def read_config(app, config_filep: str, extra_config_settings: dict):
    try:
        with open(config_filep) as yamlfile:
            config_data = yaml.load(yamlfile, Loader=yaml.FullLoader)
    except Exception:
        config_data = {}

    # Load common settings
    app.config.from_object("app.settings")
    # Load extra settings from extra_config_settings param
    app.config.update(config_data)
    # Load extra settings from extra_config_settings param
    app.config.update(extra_config_settings)

    logging.info("Force 'SQLALCHEMY_TRACK_MODIFICATIONS' to False")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    if "GRIST" not in app.config:
        logging.error("GRIST config not defined")
        exit(0)


def _load_oidc_config(app, oidc_config_filep: str):
    app.config.update(OIDC_REDIRECT_URI="*")

    oidc_conf = _read_oidc_config(oidc_config_filep)
    provider_name = next(iter(oidc_conf))

    client_metadata = oidc_conf[provider_name]["client_metadata"]
    certs_endpoint = oidc_conf[provider_name]["provider_metadata"]["jwks_endpoint"]

    auth.register_token_validator(
        KeycloakIntrospectTokenValidator(
            certs_endpoint,
            client_metadata["realm"],
            client_metadata["client_id"],
        )
    )
    app.extensions["auth"] = auth


def _read_oidc_config(oidc_config_filep: str) -> dict:
    with open(oidc_config_filep) as yamlfile:
        config_data = yaml.load(yamlfile, Loader=yaml.FullLoader)
        return config_data


def _expose_endpoint(app: Flask):
    with app.app_context():
        app.wsgi_app = ProxyFix(app.wsgi_app)
        CORS(app, resources={r"*": {"origins": "*"}})

        from app.controller.financial_data import (
            api_financial_v1,
            api_financial_v2,
        )  # pour éviter les import circulaire avec oidc
        from app.controller.laureats_data import (
            api_laureats,
        )
        from app.controller.administration import api_administration
        from app.controller.demarches import api_demarches
        from app.controller.ressource import api_ressource
        from app.controller.ref_controller import api_ref
        from app.controller.apis_externes import api_apis_externes
        from app.controller.task_management import api_task
        from app.controller.visuterritoire import api_visuterritoire_v1
        from app.controller.proxy_nocodb import (
            mount_blueprint,
        )  # pour éviter les import circulaire avec oidc

        app.register_blueprint(api_financial_v1, url_prefix="/financial-data")
        app.register_blueprint(api_financial_v2, url_prefix="/financial-data")
        app.register_blueprint(api_administration, url_prefix="/administration")
        app.register_blueprint(api_ref, url_prefix="/budget")
        app.register_blueprint(api_apis_externes, url_prefix="/apis-externes")
        app.register_blueprint(api_task, url_prefix="/task-management")
        app.register_blueprint(api_visuterritoire_v1, url_prefix="/visuterritoire")
        app.register_blueprint(api_demarches, url_prefix="/data-demarches")
        app.register_blueprint(api_ressource, url_prefix="/ressource")

        #
        app.register_blueprint(api_laureats, url_prefix="/laureats-data")

        if "NOCODB_PROJECT" in app.config:
            for project in app.config["NOCODB_PROJECT"].items():
                app.register_blueprint(mount_blueprint(project[0]), url_prefix=f"/nocodb/{project[0]}")


def _post_create_app_base(app):
    levels = {"info": logging.INFO, "debug": logging.DEBUG}
    if app.config["DEBUG"] in ["info", "debug"]:
        logging.info("Debug is enabled.")
        logging.info("SQL Logging enabled.")
        logging.getLogger().setLevel(levels[app.config["DEBUG"]])
        logging.getLogger("sqlalchemy.engine").setLevel(levels[app.config["DEBUG"]])
    else:
        logging.info("Debug is disabled or unrecognized level.")
        logging.info("SQL Logging disabled or unrecognized level.")
