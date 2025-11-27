from fastapi import FastAPI
import pytest
from fastapi.testclient import TestClient
import requests

from apis.config.Config import Config
from .fixtures.app import *  # noqa: F403
from apis.database import get_session


@pytest.fixture(scope="session")
def client(app: FastAPI):
    return TestClient(app)


@pytest.fixture()
def db_session(config):
    return get_session()


@pytest.fixture(scope="session")
def token(config: Config):  # noqa: F811
    keycloak_url = config.keycloak_openid.url
    realm = config.keycloak_openid.realm
    client_id = "bretagne.budget"

    username = config.keycloak_openid.test_user
    password = config.keycloak_openid.test_password

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
