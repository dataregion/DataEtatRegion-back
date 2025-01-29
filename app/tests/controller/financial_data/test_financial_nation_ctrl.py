import io
from tests.controller.financial_data import patching_roles


def test_missing_files(test_client):

    with patching_roles(["COMPTABLE_NATIONAL"]):
        response = test_client.post(
            "/financial-data/api/v1/national",
            data={},
            content_type="multipart/form-data",
            follow_redirects=True,
        )
        assert response.status_code == 400
        assert {"message": "Missing File", "type": "error"} == response.json


def test_not_role_comptable(test_client):
    # WITH
    file_content = b"test content"
    file = io.BytesIO(file_content)
    file.filename = "fake_file.csv"  # type: ignore

    data = {}
    data["fichierAe"] = (file, file.filename)  # type: ignore
    data["fichierCp"] = (file, file.filename)  # type: ignore

    with patching_roles(["ADMIN"]):
        response = test_client.post(
            "/financial-data/api/v1/national",
            data=data,
            content_type="multipart/form-data",
            follow_redirects=True,
        )
        assert response.status_code == 403
        assert {
            "message": "Vous n`avez pas les droits",
            "type": "error",
        } == response.json
