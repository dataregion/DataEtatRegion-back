import pytest

from apis.app import create_app
from apis.config.current import get_config, override_config

from services.tests.DataEtatPostgresContainer import DataEtatPostgresContainer


@pytest.fixture(scope="session")
def test_db():
    postgres_container = DataEtatPostgresContainer()
    postgres_container.start()
    override_config("sqlalchemy_database_uri", postgres_container.get_connection_url())
    yield postgres_container
    postgres_container.stop(force=True, delete_volume=True)


@pytest.fixture(scope="session")
def config(test_db):
    return get_config()


@pytest.fixture(scope="session")
def app(test_db, config):
    app = create_app()
    return app
