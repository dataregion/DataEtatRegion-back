from ..api_externes import apis_externes_v3  # type: ignore # noqa: F401
from tests_e2e.utils import call_request


def test_healthcheck_v3(apis_externes_v3):  # noqa: F811
    response = call_request(f"{apis_externes_v3}/healthcheck")
    assert response.status_code == 200
    assert response.json()["code"] == 200
