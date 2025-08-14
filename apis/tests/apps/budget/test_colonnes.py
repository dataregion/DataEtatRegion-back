import pytest

from tests import _assert_can_jsonize

from apis.apps.budget.services.get_colonnes import (
    get_list_colonnes_tableau,
    get_list_colonnes_grouping,
)

from fastapi.testclient import TestClient


####
#
def test_get_list_colonnes_tableau_is_serializable():
    colonnes = get_list_colonnes_tableau()
    assert colonnes is not None
    dumped = _assert_can_jsonize(colonnes, mode="json")
    assert dumped is not None


def test_get_list_colonnes_grouping_is_serializable():
    colonnes = get_list_colonnes_grouping()
    assert colonnes is not None
    dumped = _assert_can_jsonize(colonnes, mode="json")
    assert dumped is not None


#####
#
@pytest.mark.integration
def test_get_colonnes_tableau(client: TestClient, token):
    response = client.get(
        "/v3/budget/lignes?page=1&page_size=5",
        headers={"Authorization": f"Bearer {token}"},
    )
    print(response)
    assert response.status_code == 200
    assert "data" in response.json()


@pytest.mark.integration
def test_get_colonnes_grouping(client: TestClient):
    response = client.get("/v3/budget/lignes?page=1&page_size=5")
    assert response.status_code == 200
    assert "data" in response.json()
