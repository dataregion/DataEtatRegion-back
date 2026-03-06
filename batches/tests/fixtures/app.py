import pytest
from sqlalchemy import create_engine, text

from services.tests.DataEtatPostgresContainer import DataEtatPostgresContainer
from batches.config.current import get_config, override_config
from models import init as init_persistence_module
from models import Base


init_persistence_module()


def init_db_schemas(test_db, config):
    """Initialise le schéma de base de données selon SQLAlchemy."""
    # Créer les engines pour chaque base de données
    main_engine = create_engine(config.sqlalchemy_database_uri)
    audit_engine = create_engine(config.sqlalchemy_database_uri_audit, connect_args={"options": "-c search_path=audit"})
    settings_engine = create_engine(
        config.sqlalchemy_database_uri_settings, connect_args={"options": "-c search_path=settings"}
    )

    with main_engine.connect() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS audit;"))
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS settings;"))
        conn.commit()

    main_tables = [table for table in Base.metadata.tables.values() if table.schema is None]
    Base.metadata.create_all(main_engine, tables=main_tables)

    audit_tables = [table for table in Base.metadata.tables.values() if table.schema == "audit"]
    Base.metadata.create_all(audit_engine, tables=audit_tables)

    settings_table = [table for table in Base.metadata.tables.values() if table.schema == "settings"]
    Base.metadata.create_all(settings_engine, tables=settings_table)


@pytest.fixture(scope="session")
def test_db():
    postgres_container = DataEtatPostgresContainer()
    postgres_container.start()
    override_config("sqlalchemy_database_uri", postgres_container.get_connection_url())
    override_config(
        "sqlalchemy_database_uri_audit", f"{postgres_container.get_connection_url()}?options=-c%20search_path=audit"
    )
    override_config(
        "sqlalchemy_database_uri_settings",
        f"{postgres_container.get_connection_url()}?options=-c%20search_path=settings",
    )

    init_db_schemas(postgres_container, get_config())

    yield postgres_container
    postgres_container.stop(force=True, delete_volume=True)


@pytest.fixture(scope="session")
def config(test_db):
    return get_config()


@pytest.fixture(scope="session")
def app(postgres_container, config):
    # Surcharge de l'URL de la BDD, on injecte l'URL du container Postgres
    config.sqlalchemy_database_uri = postgres_container.get_connection_url()
    config.sqlalchemy_database_uri_audit = postgres_container.get_connection_url()

    yield
