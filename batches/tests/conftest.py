"""Configuration globale des tests pour le module batches.

Ce fichier est chargé automatiquement par pytest avant tous les tests.
"""

import pytest
from batches.database import get_session_main
from .fixtures.app import *  # noqa: F403


@pytest.fixture()
def db_session(config):
    return get_session_main()
