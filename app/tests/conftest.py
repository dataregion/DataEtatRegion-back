import random
import pytest
from tests.DataEtatPostgresContainer import DataEtatPostgresContainer
from sqlalchemy import text
from app import create_app_base, db


# Initialisation du conteneur PostgreSQL et récupération de l'URL de connexion
postgres_container = DataEtatPostgresContainer()
postgres_container.start()
base_url = postgres_container.get_connection_url()

# Configuration supplémentaire pour l'application Flask
extra_config = {
    "SQLALCHEMY_BINDS": {
        "settings": base_url,
        "audit": base_url,
        "demarches_simplifiees": base_url,
    },
    "SQLALCHEMY_DATABASE_URI": base_url,
    "SECRET_KEY": "secret",
    "OIDC_CLIENT_SECRETS": "ser",
    "TESTING": True,
    "SERVER_NAME": "localhost",
    "UPLOAD_FOLDER": "/tmp/",
    "IMPORT_BATCH_SIZE": 10,
}

# Création de l'application Flask
test_app = create_app_base(
    config_filep="tests/config/config.yml",
    oidc_config_filep="tests/config/oidc.yml",
    extra_config_settings=extra_config,
)

FAKER_SEED = random.randint(0, 1_000_000)


def pytest_addoption(parser):
    parser.addoption("--seed", action="store")


def pytest_report_header(config):
    global FAKER_SEED
    o_seed = config.getoption("seed")
    if o_seed is None:
        seed = FAKER_SEED
    else:
        seed = o_seed
    FAKER_SEED = int(seed)
    return f"=== Faker seed: {seed} - Launch with `pytest --seed {seed}` to reproduce"


@pytest.fixture(scope="session", autouse=True)
def setup_schemas():
    """Crée les schémas nécessaires dans PostgreSQL avant de créer les tables"""
    # Créer les schémas dans la base de données par défaut
    with test_app.app_context():
        for schema in ["settings", "audit", "demarches_simplifiees"]:
            engine = db.engines[schema]
            with engine.connect() as conn:
                conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))

    yield
    # Nettoyage après les tests
    postgres_container.stop()


@pytest.fixture(scope="session")
def app():
    return test_app


@pytest.fixture(scope="session")
def connections(app):
    with app.app_context():
        engine = db.engines[None]
        engine_settings = db.engines["settings"]
        engine_audit = db.engines["audit"]
        engine_ds = db.engines["demarches_simplifiees"]
        connections = {
            "database": engine.connect(),
            "settings": engine_settings.connect(),
            "audit": engine_audit.connect(),
            "demarches_simplifiees": engine_ds.connect(),
        }

        yield connections

        connections["database"].close()
        connections["settings"].close()
        connections["audit"].close()
        connections["demarches_simplifiees"].close()
        # Fermeture des connections et des bases
        db.session.close()
        engine.dispose()
        engine_settings.dispose()
        engine_audit.dispose()


@pytest.fixture(scope="session")
def test_client(app):
    return app.test_client()


@pytest.fixture(scope="session")
def database(app, connections, request):
    with app.app_context():
        db.create_all()
    return db


@pytest.fixture(autouse=True)
def session(connections, database, request):
    """Retourne la session à la base de données principale"""

    session = db.session
    session.begin_nested()

    def teardown():
        session.expire_all()
        session.close_all()
        session.rollback()

    request.addfinalizer(teardown)
    return session


#
# Configuration de faker
#


@pytest.fixture(scope="session", autouse=True)
def faker_seed():
    global FAKER_SEED
    return FAKER_SEED
