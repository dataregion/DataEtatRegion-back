from . import *  # noqa: F403
import pytest
from tests_e2e.utils import call_request


#########
#
def test_healthcheck(api_budget_v3):
    response = call_request(f"{api_budget_v3}/healthcheck")
    assert response.status_code == 200


#########
#
def test_financial_data_colonnes_tableau(api_budget_v3, real_token):
    response = call_request(f"{api_budget_v3}/colonnes/tableau", token=real_token)
    assert response.status_code == 200


def test_financial_data_colonnes_grouping(api_budget_v3, real_token):
    response = call_request(f"{api_budget_v3}/colonnes/grouping", token=real_token)
    assert response.status_code == 200


#########
#
@pytest.fixture(scope="function")
def lignes_first_id(api_budget_v3, real_token):
    params = {"colonnes": "id", "page_size": 1}
    response = call_request(f"{api_budget_v3}/lignes", token=real_token, params=params)
    id = response.json()["data"][0]["id"]
    return id


def test_financial_data_lignes(api_budget_v3, real_token):
    response = call_request(f"{api_budget_v3}/lignes", token=real_token)
    assert response.status_code == 200


def test_financial_data_ligne_id(api_budget_v3, lignes_first_id, real_token):
    response = call_request(
        f"{api_budget_v3}/lignes/{lignes_first_id}", token=real_token
    )
    assert response.status_code == 200


def test_financial_data_ligns_annees(api_budget_v3, lignes_first_id, real_token):
    response = call_request(f"{api_budget_v3}/lignes/annees", token=real_token)
    assert response.status_code == 200


#########
#
def test_budget_with_no_token(api_budget_v3):
    response = call_request(f"{api_budget_v3}/lignes", token=None)
    assert response.status_code == 401


def test_budget_with_bad_token(api_budget_v3, fake_token):

    response = call_request(f"{api_budget_v3}/lignes", token=fake_token)
    assert response.status_code == 401
