import pytest

__all__ = ("apis_externes_v3",)


@pytest.fixture(scope="function")
def apis_externes_v3(api_base_url):
    return f"{api_base_url}/apis-externes/v3"
