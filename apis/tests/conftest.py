from fastapi import FastAPI
import pytest
from fastapi.testclient import TestClient
from .fixtures.app import *  # noqa: F403
from apis.database import get_session_main


@pytest.fixture(scope="session")
def client(app: FastAPI):
    #
    # Par défaut on ne veut pas que le client
    # expose les exceptions du serveur, pour pouvoir tester les réponses d'erreur.
    # Davantage de détails ici: https://github.com/fastapi/fastapi/issues/2799
    #
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture()
def db_session(config):
    return get_session_main()


@pytest.fixture()
def custom_user(mock_connected_user):
    """Permet de modifier l'utilisateur pour un test spécifique."""
    # Créer une copie pour éviter de modifier l'original
    import copy

    return copy.deepcopy(mock_connected_user)
