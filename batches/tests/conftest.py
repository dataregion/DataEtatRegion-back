import os
import contextlib
import pytest
from urllib.parse import urlparse

from services.tests.DataEtatPostgresContainer import DataEtatPostgresContainer
from services.tests.DataEtatPrefectContainer import DataEtatPrefectContainer
from batches.config.current import get_config


# ------------------------------------------------------------------
# Containers
# ------------------------------------------------------------------


@pytest.fixture(scope="session")
def postgres_container():
    # Démarrage du container
    postgres = DataEtatPostgresContainer()
    postgres.start()
    try:
        yield postgres
    finally:
        postgres.stop()


@pytest.fixture(scope="session")
def prefect_container():
    # Démarrage du container, on passe le port défini dans la variable d'env
    prefect = DataEtatPrefectContainer(int(urlparse(os.environ["PREFECT_API_URL"]).port))
    prefect.start()
    try:
        yield prefect
    finally:
        prefect.stop()


# ------------------------------------------------------------------
# Environment (AVANT TOUT SQLAlchemy)
# ------------------------------------------------------------------


@pytest.fixture(scope="session")
def setup_environment(postgres_container, prefect_container):
    config = get_config()

    # Surcharge de l'URL de la BDD, on injecte l'URL du container Postgres
    config.sqlalchemy_database_uri = postgres_container.get_connection_url()
    config.sqlalchemy_database_uri_audit = postgres_container.get_connection_url()

    yield


# ------------------------------------------------------------------
# Création / destruction des tables
# ------------------------------------------------------------------


@pytest.fixture(scope="session")
def setup_database(setup_environment):
    from models import Base

    print("Tables enregistrées :", list(Base.metadata.tables.keys()))

    from batches.database import get_session_maker

    SessionMaker = get_session_maker("main")
    engine = SessionMaker.kw["bind"]

    print("CREATE_ALL tables :", list(Base.metadata.tables.keys()))
    Base.metadata.create_all(engine)

    try:
        yield
    finally:
        Base.metadata.drop_all(engine)


# ------------------------------------------------------------------
# Session SQLAlchemy par test (transaction rollback)
# ------------------------------------------------------------------


@pytest.fixture(scope="function")
def session(setup_database):
    from batches.database import get_session_maker

    SessionMaker = get_session_maker("main")
    engine = SessionMaker.kw["bind"]

    connection = engine.connect()
    transaction = connection.begin()
    db_session = SessionMaker(bind=connection)

    try:
        yield db_session
    finally:
        db_session.close()
        transaction.rollback()
        connection.close()


# ------------------------------------------------------------------
# Patch session_scope pour Prefect
# ------------------------------------------------------------------


@pytest.fixture
def patch_session_scope(session, monkeypatch):
    import batches.prefect.import_file_qpv_lieu_action as import_mod

    @contextlib.contextmanager
    def _session_scope_override():
        yield session

    monkeypatch.setattr(import_mod, "session_scope", _session_scope_override)
