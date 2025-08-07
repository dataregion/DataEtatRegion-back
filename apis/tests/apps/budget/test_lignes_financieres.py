import pytest
from fastapi.testclient import TestClient

@pytest.mark.integration
def test_lignes_financieres_list(client: TestClient):
    response = client.get("/v3/budget/lignes?page=1&page_size=5")
    assert response.status_code == 200
    assert "data" in response.json()
