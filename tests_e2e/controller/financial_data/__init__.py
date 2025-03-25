import pytest
__all__ = ("api_budget_v2",)


@pytest.fixture(scope="function")
def api_budget_v2(api_base_url):
    """ Récupère l'URL de l'API depuis CLI, ENV ou config.yaml """
    return f"{api_base_url}/financial-data/api/v2"
