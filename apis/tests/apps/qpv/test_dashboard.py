import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
def test_dashboard_data(client: TestClient):
    response = client.get("/v3/data-qpv/dashboard")
    assert response.status_code == 200
    assert "data" in response.json()
