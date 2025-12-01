from fastapi import FastAPI
import pytest
from fastapi.testclient import TestClient
from .fixtures.app import *  # noqa: F403
from apis.database import get_session


@pytest.fixture(scope="session")
def client(app: FastAPI):
    return TestClient(app)


@pytest.fixture()
def db_session(config):
    return get_session()


@pytest.fixture()
def custom_user(mock_connected_user):
    """Permet de modifier l'utilisateur pour un test spécifique."""
    # Créer une copie pour éviter de modifier l'original
    import copy

    return copy.deepcopy(mock_connected_user)
