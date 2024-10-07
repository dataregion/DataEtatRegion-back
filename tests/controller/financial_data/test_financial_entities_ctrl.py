import io
from tests import TESTS_PATH

from tests.controller.financial_data import patching_roles

_chorus_errors = TESTS_PATH / "data" / "chorus" / "errors"


def test_missing_arguments(test_client):
    file_content = b"test content"
    file = io.BytesIO(file_content)
    file.filename = "fake_file.csv"  # type: ignore

    data = {}
    data["fichierAe"] = (file, file.filename)  # type: ignore
    data["fichierCp"] = (file, file.filename)  # type: ignore
    with patching_roles(["ADMIN"]):
        response = test_client.post(
            "/financial-data/api/v1/ae-cp", data=data, content_type="multipart/form-data", follow_redirects=True
        )
        assert response.status_code == 400
        assert {"message": "Missing Argument annee", "type": "error"} == response.json

        response_missing_file = test_client.post(
            "/financial-data/api/v1/ae-cp", data={}, content_type="multipart/form-data", follow_redirects=True
        )
        assert response_missing_file.status_code == 400
        assert {"message": "Missing Argument annee", "type": "error"} == response_missing_file.json


def test_not_role(test_client):
    # WITH
    file_content = b"test content"
    file = io.BytesIO(file_content)
    file.filename = "fake_file.csv"  # type: ignore

    data = {}
    data["fichierAe"] = (file, file.filename)  # type: ignore
    data["fichierCp"] = (file, file.filename)  # type: ignore

    with patching_roles([]):
        response = test_client.post(
            "/financial-data/api/v1/ae-cp", data=data, content_type="multipart/form-data", follow_redirects=True
        )
        assert response.status_code == 403
        assert {"message": "Vous n`avez pas les droits", "type": "error"} == response.json


def test_bad_file(test_client):
    data = {"annee": 2023}
    with patching_roles(["ADMIN"]):
        with open(_chorus_errors / "sample.pdf", "rb") as f:
            data["fichierAe"] = (f, "filename.csv")  # type: ignore
            data["fichierCp"] = (f, "filename.csv")  # type: ignore
            response = test_client.post(
                "/financial-data/api/v1/ae-cp", data=data, content_type="multipart/form-data", follow_redirects=True
            )

            assert response.status_code == 400
            assert response.json["type"] == "error", "Le payload doit contenir 'type' = 'error'"


def test_file_missing_column(test_client):
    data = {"annee": 2023}
    with patching_roles(["ADMIN"]):
        with open(_chorus_errors / "chorus_ae_missing_column.csv", "rb") as f:
            data["fichierAe"] = (f, "filename.csv")  # type: ignore
            data["fichierCp"] = (f, "filename.csv")  # type: ignore
            response = test_client.post(
                "/financial-data/api/v1/ae-cp", data=data, content_type="multipart/form-data", follow_redirects=True
            )

            assert response.status_code == 400
            assert response.json["type"] == "error", "Le payload doit contenir 'type' = 'error'"
