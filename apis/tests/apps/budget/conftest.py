"""Fixtures pour les tests du module budget."""

from ...fixtures.app import (
    app as _test_app,  # noqa: F401
    patch_keycloak_validator,  # noqa: F401
)

import pytest
from models.connected_user import ConnectedUser


@pytest.fixture(scope="session")
def mock_connected_user():
    """Crée un ConnectedUser pour les tests avec les métadonnées de région."""
    return ConnectedUser(
        {
            "azp": "test-client-id",
            "sub": "test-user-123",
            "email": "test@example.com",
            "preferred_username": "testuser",
            "realm_access": {"roles": ["user", "admin"]},
            "resource_access": {
                "test-client-id": {"roles": ["users"]},
            },
            "roles_meta": {
                "test-client-id": {
                    "users": {
                        "region": "53",  # Bretagne
                    }
                }
            },
        }
    )


@pytest.fixture(scope="session")
def app(_test_app, patch_keycloak_validator):  # noqa: F811
    """App avec le validator Keycloak patché pour les tests."""
    return _test_app
