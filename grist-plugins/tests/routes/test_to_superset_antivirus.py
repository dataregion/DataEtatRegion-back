import json
from unittest.mock import AsyncMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from grist_plugins.routes import to_superset
from services.antivirus import AntivirusScanError, VirusFoundError


class _FakeSupersetService:
    def __init__(self) -> None:
        self.check_user_exists = AsyncMock(return_value=True)
        self.import_table = AsyncMock(
            return_value={
                "message": "ok",
                "rows_imported": 1,
            }
        )


@pytest.fixture()
def client() -> TestClient:
    app = FastAPI()
    app.include_router(to_superset.router)
    return TestClient(app, raise_server_exceptions=False)


def _payload() -> dict[str, str]:
    return {
        "tableId": "ma_table",
        "columns": json.dumps(
            [
                {
                    "id": "col1",
                    "type": "Text",
                    "is_index": False,
                }
            ]
        ),
    }


def _headers() -> dict[str, str]:
    return {"Authorization": "Bearer test-token"}


def _file_payload() -> dict[str, tuple[str, bytes, str]]:
    return {
        "file": (
            "data.csv",
            b"col1\nvalue1\n",
            "text/csv",
        )
    }


def test_publish_rejects_infected_file(client: TestClient) -> None:
    fake_service = _FakeSupersetService()

    with (
        patch.object(to_superset, "get_superset_service", return_value=fake_service),
        patch.object(
            to_superset.AntivirusService,
            "scan_file",
            side_effect=VirusFoundError("Eicar-Test-Signature"),
        ),
    ):
        response = client.post(
            "/to-superset/publish",
            headers=_headers(),
            data=_payload(),
            files=_file_payload(),
        )

    assert response.status_code == 400
    assert "un virus" in response.json()["message"].lower()
    fake_service.import_table.assert_not_called()


def test_publish_rejects_when_antivirus_unavailable(client: TestClient) -> None:
    fake_service = _FakeSupersetService()

    with (
        patch.object(to_superset, "get_superset_service", return_value=fake_service),
        patch.object(
            to_superset.AntivirusService,
            "scan_file",
            side_effect=AntivirusScanError("Le service antivirus est indisponible"),
        ),
    ):
        response = client.post(
            "/to-superset/publish",
            headers=_headers(),
            data=_payload(),
            files=_file_payload(),
        )

    assert response.status_code == 500
    fake_service.import_table.assert_not_called()


def test_publish_keeps_existing_behavior_when_file_is_clean(client: TestClient) -> None:
    fake_service = _FakeSupersetService()

    with (
        patch.object(to_superset, "get_superset_service", return_value=fake_service),
        patch.object(to_superset.AntivirusService, "scan_file", return_value=None),
    ):
        response = client.post(
            "/to-superset/publish",
            headers=_headers(),
            data=_payload(),
            files=_file_payload(),
        )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["table_id"] == "ma_table"
    fake_service.import_table.assert_awaited_once()
