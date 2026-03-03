"""Fixtures pour les tests du module budget."""

from ...fixtures.app import (
    app as _test_app,  # noqa: F401
    patch_keycloak_validator,  # noqa: F401
)

import pytest


@pytest.fixture(scope="session")
def app(_test_app, patch_keycloak_validator):  # noqa: F811
    """App avec le validator Keycloak patché pour les tests."""
    return _test_app
