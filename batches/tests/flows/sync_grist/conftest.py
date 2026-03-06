"""Fixtures pour les tests du module sync_grist."""

from ...fixtures.app import (
    app as _test_app,  # noqa: F401
)

import pytest
from batches.database import get_session_main

########################################################
# App & Database
########################################################


@pytest.fixture(scope="session")
def app(_test_app):  # noqa: F811
    """Configure l'app pour les tests (sans container Prefect, mode unit test)."""
    return _test_app


@pytest.fixture
def session(test_db):
    """Crée une session SQLAlchemy pour les tests."""
    gen = get_session_main()
    session = next(gen)
    try:
        yield session
    finally:
        try:
            next(gen)
        except StopIteration:
            pass
