import pytest

__all__ = ("api_administration",)


@pytest.fixture(scope="function")
def api_administration(api_base_url):
    return f"{api_base_url}/administration/api/v1"