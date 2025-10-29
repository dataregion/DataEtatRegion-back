import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
def test_map_data(client: TestClient):
    response = client.get("/v3/data-qpv/map")
    assert response.status_code == 200
    assert "data" in response.json()
