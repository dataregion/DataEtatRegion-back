from . import *  # noqa: F403
from tests_e2e.utils import call_request


def test_import_national_with_fake_token(api_budget_v1, fake_token):
    response = call_request(f"{api_budget_v1}/national", method="POST", token=fake_token)
    assert response.status_code == 403
    assert response.json() == {"message": "Forbidden", "type": "error"}


def test_import_regional_with_fake_token(api_budget_v1, fake_token):
    response = call_request(f"{api_budget_v1}/region", method="POST", token=fake_token)
    assert response.status_code == 403
    assert response.json() == {"message": "Forbidden", "type": "error"}
