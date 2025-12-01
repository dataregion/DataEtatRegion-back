import pytest

from apis.app import create_app
from apis.config.current import get_config, override_config
from services.tests.DataEtatPostgresContainer import DataEtatPostgresContainer
from models.connected_user import ConnectedUser


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
def mock_connected_user():
    """Crée un ConnectedUser pour les tests."""
    return ConnectedUser(
        {
            "sub": "test-user-123",
            "email": "test@example.com",
            "preferred_username": "testuser",
            "realm_access": {"roles": ["user", "admin"]},
        }
    )


@pytest.fixture(scope="session", autouse=True)
def patch_keycloak_validator(mock_connected_user):
    """Patch KeycloakTokenValidator pour les tests."""
    from apis.security.keycloak_token_validator import KeycloakTokenValidator

    # Sauvegarder la méthode originale
    original_validate_token = KeycloakTokenValidator.validate_token

    # Créer la méthode mockée
    def mock_validate_token(self, token: str) -> ConnectedUser:
        """Mock qui retourne toujours le même utilisateur."""
        return mock_connected_user

    # Remplacer la méthode
    KeycloakTokenValidator.validate_token = mock_validate_token
    yield
    # Restaurer après tous les tests
    KeycloakTokenValidator.validate_token = original_validate_token


@pytest.fixture(scope="session")
def app(test_db, config):
    app = create_app()
    return app
