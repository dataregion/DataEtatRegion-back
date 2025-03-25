import requests
from . import *  # noqa: F403
from tests_e2e import TESTS_PATH


def test_healthcheck(api_budget_v2):
    response = requests.get(f"{api_budget_v2}/budget/healthcheck")
    assert response.status_code == 200
    assert response.json() == 200


def test_budget_with_no_token(api_budget_v2):
    response = requests.get(f"{api_budget_v2}/budget")
    assert response.status_code == 401

def test_budget_with_bad_token(api_budget_v2, fake_token):
    response = requests.get(f"{api_budget_v2}/budget",  
                            headers = {
            "accept": "application/json",
            "content-yype": "application/json",
            "authorization": f"Bearer {fake_token}"
        })
    assert response.status_code == 403
    assert response.json() == {'message': 'Forbidden', 'type': 'error'}
