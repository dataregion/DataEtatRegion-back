import pytest
from fastapi.testclient import TestClient
import requests

from services.tests.DataEtatPostgresContainer import DataEtatPostgresContainer
from apis.config.current import get_config, override_config

################################################
# XXX: il est important de faire cela avant l'initialisation de l'application
# Initialisation du conteneur PostgreSQL et récupération de l'URL de connexion
postgres_container = DataEtatPostgresContainer()
postgres_container.start()
base_url = postgres_container.get_connection_url()

override_config("sqlalchemy_database_uri", base_url)
################################################

from apis.main import app  # noqa: E402
from tests.fixtures.db import get_test_db  # noqa: E402


@pytest.fixture(scope="session")
def client():
    return TestClient(app)


@pytest.fixture
def db_session():
    return get_test_db()


@pytest.fixture(scope="session")
def token():
    keycloak_url = get_config().keycloak_openid.url
    realm = get_config().keycloak_openid.realm
    client_id = "bretagne.budget"

    username = get_config().keycloak_openid.test_user
    password = get_config().keycloak_openid.test_password

    token_url = f"{keycloak_url}/realms/{realm}/protocol/openid-connect/token"

    response = requests.post(
        token_url,
        data={
            "grant_type": "password",
            "client_id": client_id,
            "username": username,
            "password": password,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    print(response.content)
    response.raise_for_status()
    return response.json()["access_token"]
