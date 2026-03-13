"""Fixtures communes pour les tests de flows Prefect."""

import pytest
from prefect.testing.utilities import prefect_test_harness


@pytest.fixture(autouse=True, scope="session")
def prefect_test_fixture():
    """Exécute les flows/tasks sur un backend Prefect de test éphémère."""
    with prefect_test_harness():
        yield
