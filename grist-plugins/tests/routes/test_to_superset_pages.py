from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from grist_plugins.routes import to_superset


@pytest.fixture()
def client() -> TestClient:
    app = FastAPI()
    app.include_router(to_superset.router)
    return TestClient(app)


@pytest.mark.parametrize("path", ["/callback", "/to-superset"])
def test_page_renders(client: TestClient, path: str) -> None:
    response = client.get(path)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
