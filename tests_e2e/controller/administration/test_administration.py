from . import *  # noqa: F403
from tests_e2e import TESTS_PATH
from tests_e2e.utils import call_request


def test_get_audit_with_fake_token(api_administration,fake_token):
    response = call_request(f"{api_administration}/audit/FINANCIAL_DATA_AE", token=fake_token)
    assert response.status_code == 403
    assert response.json() ==  {"message": "Forbidden", "type": "error"}


def test_get_audit_with_no_token(api_administration):
    response = call_request(f"{api_administration}/audit/FINANCIAL_DATA_AE")
    assert response.status_code == 401