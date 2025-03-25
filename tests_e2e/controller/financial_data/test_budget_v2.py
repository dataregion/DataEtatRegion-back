from . import *  # noqa: F403
from tests_e2e import TESTS_PATH
from tests_e2e.utils import call_request


def test_healthcheck(api_budget_v2):
    response = call_request(f"{api_budget_v2}/budget/healthcheck")
    assert response.status_code == 200
    assert response.json() == 200


def test_budget_with_no_token(api_budget_v2):
    response = call_request(f"{api_budget_v2}/budget", token=None)
    assert response.status_code == 401


def test_budget_with_bad_token(api_budget_v2, fake_token):

    response = call_request(f"{api_budget_v2}/budget", token=fake_token)
    assert response.status_code == 403
    assert response.json() == {"message": "Forbidden", "type": "error"}
