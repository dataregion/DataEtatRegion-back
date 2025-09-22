from http import HTTPStatus
from tests_e2e.utils import call_request
from requests import Response


import pytest
import jwt
from collections import namedtuple


PremiereLigneInfo = namedtuple("PremiereLigneInfo", ["id", "source"])


@pytest.fixture(scope="function")
def premiere_ligne_info(api_budget_v3, real_token) -> PremiereLigneInfo:
    params = {"page_size": 1}
    response = call_request(f"{api_budget_v3}/lignes", token=real_token, params=params)
    ligne_data = response.json()["data"]["lignes"][0]
    return PremiereLigneInfo(id=ligne_data["id"], source=ligne_data["source"])


def unsafe_jwt_decode(token):
    decoded = jwt.decode(token, options={"verify_signature": False})
    return decoded


def sanitize_region(region: str):
    return region.removeprefix("0")


def assert_api_response_status(response: Response, status: int):
    """
    S'assure que le status de la réponse correspond au code.
    Vérifie également les paramètres 'code' et 'success' du flux de réponse
    """
    assert response.status_code == status
    if status == HTTPStatus.NO_CONTENT:
        return
    assert response.json()["code"] == status

    #
    if status >= 200 and status < 300:
        assert response.json()["success"] is True
    else:
        assert response.json()["success"] is False
