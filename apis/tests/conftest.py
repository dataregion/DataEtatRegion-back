import os
import pytest
from fastapi.testclient import TestClient
import requests
import yaml

from apis.config import config
from apis.main import app

from tests.fixtures.db import get_test_db


def load_test_config():
    config_path = os.path.join(os.path.dirname(__file__), "config.yml")
    with open(config_path, "r") as file:
        return yaml.safe_load(file)

test_config = load_test_config()

@pytest.fixture(scope="session")
def client():
    return TestClient(app)

@pytest.fixture
def db_session():
    return get_test_db()

@pytest.fixture(scope="session")
def token():
    keycloak_url = config["KEYCLOAK_OPENID"]["URL"]
    realm = config["KEYCLOAK_OPENID"]["REALM"]
    client_id = "bretagne.budget"

    username = test_config["TEST_USER"]
    password = test_config["TEST_PASSWORD"]

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
