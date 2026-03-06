"""Fixtures pour les tests du module administration."""

import contextlib

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
def patch_session_scope(session, monkeypatch):
    import batches.prefect.import_file_qpv_lieu_action as import_mod

    @contextlib.contextmanager
    def _session_scope_override():
        yield session

    monkeypatch.setattr(import_mod, "session_scope", _session_scope_override)


########################################################


@pytest.fixture
def session(test_db):
    gen = get_session_main()
    session = next(gen)
    try:
        yield session
    finally:
        try:
            next(gen)
        except StopIteration:
            pass
