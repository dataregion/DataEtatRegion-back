"""Configuration globale des tests pour le module batches.

Ce fichier est chargé automatiquement par pytest avant tous les tests.
Il contient notamment les mocks Prefect nécessaires pour les tests unitaires.
"""

import logging
import sys
from unittest.mock import MagicMock
from uuid import uuid4
import pytest
from batches.database import get_session_main
from .fixtures.app import *  # noqa: F403


# ============================================================================
# Mock Prefect pour mode UNIT TEST (sans containers)
# ============================================================================
# Ces mocks doivent être définis AVANT tout import de code utilisant Prefect


def mock_decorator(*args, **kwargs):
    """Mock pour @flow et @task qui retourne la fonction telle quelle."""

    def decorator(func):
        return func

    if len(args) == 1 and callable(args[0]):
        return decorator(args[0])
    return decorator


# Patcher prefect avant tout import
if "prefect" not in sys.modules:
    sys.modules["prefect"] = MagicMock()
sys.modules["prefect"].flow = mock_decorator
sys.modules["prefect"].task = mock_decorator
sys.modules["prefect"].get_run_logger = MagicMock(return_value=logging.getLogger("prefect.test"))

# Mock runtime avec flow_run.id qui retourne un UUID valide
mock_runtime = MagicMock()
mock_runtime.flow_run.id = str(uuid4())
sys.modules["prefect"].runtime = mock_runtime

# Mock get_run_logger pour retourner un logger standard
prefect_logging = MagicMock()
prefect_logging.get_run_logger = MagicMock(return_value=logging.getLogger("prefect.test"))
sys.modules["prefect.logging"] = prefect_logging

# Mock cache_policies (utilisé dans sync_referentiel_grist)
prefect_cache_policies = MagicMock()
prefect_cache_policies.NO_CACHE = MagicMock()
sys.modules["prefect.cache_policies"] = prefect_cache_policies

# ============================================================================


@pytest.fixture()
def db_session(config):
    return get_session_main()
