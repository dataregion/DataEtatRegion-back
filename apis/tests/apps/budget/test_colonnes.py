import pytest

from fastapi.testclient import TestClient


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
