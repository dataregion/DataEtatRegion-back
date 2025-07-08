import pytest

__all__ = (
    "api_budget_v1",
    "api_budget_v2",
)


@pytest.fixture(scope="function")
def api_budget_v1(api_base_url):
    return f"{api_base_url}/financial-data/api/v1"


@pytest.fixture(scope="function")
def api_budget_v2(api_base_url):
    return f"{api_base_url}/financial-data/api/v2"
