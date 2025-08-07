import pytest

from apis.app import create_app
from apis.config.current import get_config, override_config

from services.tests.DataEtatPostgresContainer import DataEtatPostgresContainer


@pytest.fixture(scope="session")
def test_db():
    postgres_container = DataEtatPostgresContainer()
    postgres_container.start()
    return postgres_container


@pytest.fixture(scope="session")
def config(test_db):
    override_config("sqlalchemy_database_uri", test_db.get_connection_url())
    return get_config()


@pytest.fixture(scope="session")
def app(config):
    app = create_app()
    return app
