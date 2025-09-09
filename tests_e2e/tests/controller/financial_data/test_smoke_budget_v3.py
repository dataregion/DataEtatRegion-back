from . import *  # noqa: F403
from tests_e2e.utils import call_request

from .utils_test_budget_v3 import (
    lignes_first_id,  # noqa: F401
    assert_api_response_status,
)


#########
#
def test_smoke_healthcheck(api_budget_v3):
    response = call_request(f"{api_budget_v3}/healthcheck")
    assert_api_response_status(response, 200)


#########
# Colonnes
def test_smoke_financial_data_colonnes_tableau(api_budget_v3, real_token):
    response = call_request(f"{api_budget_v3}/colonnes/tableau", token=real_token)
    assert_api_response_status(response, 200)


def test_smoke_financial_data_colonnes_grouping(api_budget_v3, real_token):
    response = call_request(f"{api_budget_v3}/colonnes/grouping", token=real_token)
    assert_api_response_status(response, 200)


#########
# API lignes financières
def test_smoke_financial_data_lignes(api_budget_v3, real_token):
    response = call_request(f"{api_budget_v3}/lignes", token=real_token)
    assert_api_response_status(response, 200)


def test_smoke_financial_data_ligne_id(
    api_budget_v3, lignes_first_id, real_token  # noqa F811
):
    response = call_request(
        f"{api_budget_v3}/lignes/{lignes_first_id}?source=FINANCIAL_DATA_CP",
        token=real_token,
    )
    assert_api_response_status(response, 200)


def test_smoke_financial_data_lignes_annees(api_budget_v3, real_token):
    response = call_request(f"{api_budget_v3}/lignes/annees", token=real_token)
    assert_api_response_status(response, 200)
