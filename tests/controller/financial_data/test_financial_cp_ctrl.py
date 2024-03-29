import io
from tests import TESTS_PATH

from tests.controller.financial_data import patching_roles

_chorus = TESTS_PATH / "data" / "chorus"
_chorus_errors = _chorus / "errors"


def test_missing_arguments(test_client):
    file_content = b"test content"
    file = io.BytesIO(file_content)
    file.filename = "fake_file.csv"

    data = {}
    data["fichier"] = (file, file.filename)
    with patching_roles(["ADMIN"]):
        response = test_client.post(
            "/financial-data/api/v1/cp", data=data, content_type="multipart/form-data", follow_redirects=True
        )
        assert response.status_code == 400
        assert {"message": "Missing Argument annee", "type": "error"} == response.json

        response_missing_file = test_client.post(
            "/financial-data/api/v1/cp", data={}, content_type="multipart/form-data", follow_redirects=True
        )
        assert response_missing_file.status_code == 400
        assert {"message": "Missing Argument annee", "type": "error"} == response_missing_file.json


def test_not_role(test_client):
    # WITH
    file_content = b"test content"
    file = io.BytesIO(file_content)
    file.filename = "fake_file.csv"

    data = {}
    data["fichier"] = (file, file.filename)
    with patching_roles([]):
        response = test_client.post(
            "/financial-data/api/v1/cp", data=data, content_type="multipart/form-data", follow_redirects=True
        )
        assert response.status_code == 403
        assert {"message": "Vous n`avez pas les droits", "type": "error"} == response.json


def test_bad_file(test_client):
    data = {"code_region": "35", "annee": 2023}
    with patching_roles(["ADMIN"]):
        with open(_chorus_errors / "sample.pdf", "rb") as f:
            data["fichier"] = (f, "filename.csv")
            response = test_client.post(
                "/financial-data/api/v1/cp", data=data, content_type="multipart/form-data", follow_redirects=True
            )

            assert response.status_code == 400
            assert {"message": "Erreur de lecture du fichier", "type": "error"} == response.json


def test_file_missing_column(test_client):
    data = {"code_region": "35", "annee": 2023}
    with patching_roles(["ADMIN"]):
        with open(_chorus / "chorus_ae.csv", "rb") as f:
            data["fichier"] = (f, f.name)
            response = test_client.post(
                "/financial-data/api/v1/cp", data=data, content_type="multipart/form-data", follow_redirects=True
            )

            assert response.status_code == 400
            assert {"message": "Le fichier n'a pas les bonnes colonnes", "type": "error"} == response.json
