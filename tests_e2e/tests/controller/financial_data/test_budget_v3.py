from . import *  # noqa: F403
from tests_e2e.utils import call_request


def test_healthcheck(api_budget_v3):
    response = call_request(f"{api_budget_v3}/healthcheck")
    assert response.status_code == 200
    assert response.json() == 200


def test_budget_with_no_token(api_budget_v3):
    response = call_request(f"{api_budget_v3}/lignes", token=None)
    assert response.status_code == 401


def test_budget_with_bad_token(api_budget_v3, fake_token):

    response = call_request(f"{api_budget_v3}/lignes", token=fake_token)
    assert response.status_code == 403
    assert response.json() == {"message": "Forbidden", "type": "error"}
