import io
import json
from models.value_objects.to_superset import ColumnIn, ColumnType
from apis.apps.grist_to_superset.models.publish_response import PublishResponse

from tests import _assert_can_jsonize


# Données de test
VALID_COLUMNS = [
    {"id": "name", "type": "Text", "is_index": True},
    {"id": "age", "type": "Numeric", "is_index": False},
    {"id": "email", "type": "Text", "is_index": False},
]

VALID_CSV_CONTENT = """name,age,email
Alice,30,alice@example.com
Bob,25,bob@example.com
Charlie,35,charlie@example.com"""


def create_csv_file(content: str):
    """Helper pour créer un fichier CSV en mémoire."""
    return io.BytesIO(content.encode())


# ============================================================================
# TESTS UNITAIRES
# ============================================================================


def test_column_schema_is_serializable():
    """Test que le schéma de colonne est sérialisable en JSON."""

    column = ColumnIn(id="test_col", type=ColumnType.TEXT, is_index=True)
    dumped = _assert_can_jsonize(column, mode="json")
    assert dumped is not None


def test_publish_response_is_serializable():
    """Test que la réponse de publication est sérialisable en JSON."""

    response = PublishResponse(success=True, message="Import réussi", table_id="test_table", rows_imported=10)
    dumped = _assert_can_jsonize(response, mode="json")
    assert dumped is not None


# ============================================================================
# TESTS D'AUTHENTIFICATION
# ============================================================================


def test_import_without_token(client):
    """Test sans token API - doit retourner 403."""
    files = {"file": ("test.csv", create_csv_file(VALID_CSV_CONTENT), "text/csv")}
    data = {"table_id": "test_table", "columns": json.dumps(VALID_COLUMNS)}

    response = client.post("grist-to-superset/api/v3/import/table", data=data, files=files)
    assert response.status_code == 403


def test_import_with_invalid_token(client):
    """Test avec un token invalide - doit retourner 401."""
    files = {"file": ("test.csv", create_csv_file(VALID_CSV_CONTENT), "text/csv")}
    data = {"table_id": "test_table", "columns": json.dumps(VALID_COLUMNS)}

    response = client.post(
        "grist-to-superset/api/v3/import/table", data=data, files=files, headers={"X-API-Key": "invalid_token"}
    )
    assert response.status_code == 401
    assert "detail" in response.json()


def test_import_with_empty_token(client):
    """Test avec un token vide - doit retourner 403."""
    files = {"file": ("test.csv", create_csv_file(VALID_CSV_CONTENT), "text/csv")}
    data = {"table_id": "test_table", "columns": json.dumps(VALID_COLUMNS)}

    response = client.post("grist-to-superset/api/v3/import/table", data=data, files=files, headers={"X-API-Key": ""})
    assert response.status_code == 403


# ============================================================================
# TESTS DE VALIDATION DES FICHIERS
# ============================================================================


def test_import_with_non_csv_file(client, config):
    """Test avec un fichier non-CSV - doit retourner 400."""
    files = {"file": ("test.txt", io.BytesIO(b"not a csv"), "text/plain")}
    data = {"table_id": "test_table", "columns": json.dumps(VALID_COLUMNS)}

    response = client.post(
        "grist-to-superset/api/v3/import/table",
        data=data,
        files=files,
        headers={"X-API-Key": config.token_for_grist_plugins, "Authorization": "Bearer fake-token-for-test"},
    )
    assert response.status_code == 400
    assert "CSV" in response.json()["detail"]


def test_import_with_empty_csv(client, config):
    """Test avec un CSV vide - doit retourner une erreur."""
    files = {"file": ("empty.csv", create_csv_file(""), "text/csv")}
    data = {"table_id": "test_table", "columns": json.dumps(VALID_COLUMNS)}

    response = client.post(
        "grist-to-superset/api/v3/import/table",
        data=data,
        files=files,
        headers={"X-API-Key": config.token_for_grist_plugins, "Authorization": "Bearer fake-token-for-test"},
    )
    assert response.status_code == 400
    assert response.json()["message"] == "Le fichier CSV est vide"


# ============================================================================
# TESTS DE VALIDATION DES COLONNES
# ============================================================================


def test_import_with_invalid_json_columns(client, config):
    """Test avec un JSON invalide pour les colonnes - doit retourner 422."""
    files = {"file": ("test.csv", create_csv_file(VALID_CSV_CONTENT), "text/csv")}
    data = {"table_id": "test_table", "columns": "invalid json {["}

    response = client.post(
        "grist-to-superset/api/v3/import/table",
        data=data,
        files=files,
        headers={"X-API-Key": config.token_for_grist_plugins, "Authorization": "Bearer fake-token-for-test"},
    )
    assert response.status_code == 422
    assert "JSON" in response.json()["message"]


def test_import_with_missing_columns_in_csv(client, config):
    """Test avec des colonnes manquantes dans le CSV - doit retourner 400."""
    columns_with_missing = [
        {"id": "name", "type": "Text", "is_index": True},
        {"id": "missing_column", "type": "Text", "is_index": False},
    ]
    files = {"file": ("test.csv", create_csv_file(VALID_CSV_CONTENT), "text/csv")}
    data = {"table_id": "test_table", "columns": json.dumps(columns_with_missing)}

    response = client.post(
        "grist-to-superset/api/v3/import/table",
        data=data,
        files=files,
        headers={"X-API-Key": config.token_for_grist_plugins, "Authorization": "Bearer fake-token-for-test"},
    )
    assert response.status_code == 400
    assert "colonnes manquantes dans le csv: missing_column" in response.json()["message"].lower()


def test_import_with_invalid_column_type(client, config):
    """Test avec un type de colonne invalide."""
    invalid_columns = [{"id": "name", "type": "invalid_type", "is_index": True}]
    files = {"file": ("test.csv", create_csv_file(VALID_CSV_CONTENT), "text/csv")}
    data = {"table_id": "test_table", "columns": json.dumps(invalid_columns)}

    response = client.post(
        "grist-to-superset/api/v3/import/table",
        data=data,
        files=files,
        headers={"X-API-Key": config.token_for_grist_plugins, "Authorization": "Bearer fake-token-for-test"},
    )
    assert response.status_code in [422, 400]


# ============================================================================
# TESTS DE VALIDATION DES PARAMÈTRES
# ============================================================================


def test_import_missing_table_id(client, config):
    """Test sans table_id - doit retourner 422."""
    files = {"file": ("test.csv", create_csv_file(VALID_CSV_CONTENT), "text/csv")}
    data = {"columns": json.dumps(VALID_COLUMNS)}

    response = client.post(
        "grist-to-superset/api/v3/import/table",
        data=data,
        files=files,
        headers={"X-API-Key": config.token_for_grist_plugins, "Authorization": "Bearer fake-token-for-test"},
    )
    assert response.status_code == 422


def test_import_missing_columns(client, config):
    """Test sans columns - doit retourner 422."""
    files = {"file": ("test.csv", create_csv_file(VALID_CSV_CONTENT), "text/csv")}
    data = {"table_id": "test_table"}

    response = client.post(
        "grist-to-superset/api/v3/import/table",
        data=data,
        files=files,
        headers={"X-API-Key": config.token_for_grist_plugins, "Authorization": "Bearer fake-token-for-test"},
    )
    assert response.status_code == 422


def test_import_missing_file(client, config):
    """Test sans fichier - doit retourner 422."""
    data = {"table_id": "test_table", "columns": json.dumps(VALID_COLUMNS)}

    response = client.post(
        "grist-to-superset/api/v3/import/table",
        data=data,
        headers={"X-API-Key": config.token_for_grist_plugins, "Authorization": "Bearer fake-token-for-test"},
    )
    assert response.status_code == 422


# ============================================================================
# TESTS PASSANTS
# ============================================================================


def test_import_successful(client, config):
    """Test d'import réussi avec données valides."""
    files = {"file": ("test.csv", create_csv_file(VALID_CSV_CONTENT), "text/csv")}
    data = {"table_id": "test_table", "columns": json.dumps(VALID_COLUMNS)}

    response = client.post(
        "grist-to-superset/api/v3/import/table",
        data=data,
        files=files,
        headers={"X-API-Key": config.token_for_grist_plugins, "Authorization": "Bearer fake-token-for-test"},
    )
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["table_id"] == "test_table"
    assert response.json()["rows_imported"] == 3


def test_import_single_row(client, config):
    """Test d'import avec une seule ligne."""
    single_row_csv = """name,age,email
Alice,30,alice@example.com"""

    files = {"file": ("test.csv", create_csv_file(single_row_csv), "text/csv")}
    data = {"table_id": "single_table", "columns": json.dumps(VALID_COLUMNS)}

    response = client.post(
        "grist-to-superset/api/v3/import/table",
        data=data,
        files=files,
        headers={"X-API-Key": config.token_for_grist_plugins, "Authorization": "Bearer fake-token-for-test"},
    )
    assert response.status_code == 200
    assert response.json()["rows_imported"] == 1


def test_import_subset_columns(client, config):
    """Test d'import avec un sous-ensemble de colonnes."""
    subset_columns = [
        {"id": "name", "type": "Text", "is_index": True},
        {"id": "age", "type": "Numeric", "is_index": False},
    ]

    files = {"file": ("test.csv", create_csv_file(VALID_CSV_CONTENT), "text/csv")}
    data = {"table_id": "subset_table", "columns": json.dumps(subset_columns)}

    response = client.post(
        "grist-to-superset/api/v3/import/table",
        data=data,
        files=files,
        headers={"X-API-Key": config.token_for_grist_plugins, "Authorization": "Bearer fake-token-for-test"},
    )
    assert response.status_code == 200
    result = response.json()
    assert "success" in result
    assert "message" in result
    assert "table_id" in result
    assert "rows_imported" in result
    assert result["rows_imported"] == 3
