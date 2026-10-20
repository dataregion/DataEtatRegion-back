import json
from unittest.mock import MagicMock, patch

import pytest

from apis.apps.grist_to_superset.exceptions.import_data_exceptions import (
    InvalidGristDocIdException,
    InvalidTableIdException,
    PublishedTableNameTooLongException,
)
from apis.apps.grist_to_superset.services.published_table import (
    POSTGRES_IDENTIFIER_MAX_LENGTH,
    build_published_table_name,
)

DOC_ID = "mXq3vB7kPz9WcR2aLtN4Ue"
OTHER_DOC_ID = "Zz9yX8wV7uT6sR5qP4oN3m"
FORK_DOC_ID = f"{DOC_ID}~f0rkId~5"

ROUTER = "apis.apps.grist_to_superset.routers.grist_to_superset"


def test_published_table_name_is_suffixed_by_doc_id():
    assert build_published_table_name("Budget", DOC_ID) == f"Budget_{DOC_ID}"


def test_same_table_of_two_documents_does_not_collide():
    assert build_published_table_name("Budget", DOC_ID) != build_published_table_name("Budget", OTHER_DOC_ID)


def test_fork_is_published_apart_from_its_document():
    assert build_published_table_name("Budget", FORK_DOC_ID) == f"Budget_{FORK_DOC_ID}"


def test_table_id_at_limit_is_accepted():
    table_id = "T" * (POSTGRES_IDENTIFIER_MAX_LENGTH - len(DOC_ID) - 1)
    assert len(build_published_table_name(table_id, DOC_ID)) == POSTGRES_IDENTIFIER_MAX_LENGTH


def test_name_over_postgres_limit_is_refused():
    with pytest.raises(PublishedTableNameTooLongException, match="40 caractères"):
        build_published_table_name("T" * 41, DOC_ID)


def test_fork_with_long_table_id_is_refused_instead_of_truncated():
    with pytest.raises(PublishedTableNameTooLongException):
        build_published_table_name("T" * 40, FORK_DOC_ID)


@pytest.mark.parametrize("doc_id", ["", "tooShort", "cKjL2zrDMMRw", 'mXq3vB7kPz9WcR2aLtN4U"', f"{DOC_ID}~"])
def test_invalid_doc_id_is_refused(doc_id):
    with pytest.raises(InvalidGristDocIdException):
        build_published_table_name("Budget", doc_id)


@pytest.mark.parametrize("table_id", ["", 'Budget"; DROP TABLE x; --', "Budget-2025", "Budgét"])
def test_invalid_table_id_is_refused(table_id):
    with pytest.raises(InvalidTableIdException):
        build_published_table_name(table_id, DOC_ID)


def _headers(config):
    return {"X-API-Key": config.token_for_grist_plugins, "Authorization": "Bearer fake-token-for-test"}


def test_import_writes_the_published_table(client, config):
    with patch(f"{ROUTER}.ImportService") as import_service:
        import_service.return_value.import_table.return_value = 1
        response = client.post(
            "grist-to-superset/api/v3/import/table",
            data={
                "doc_id": DOC_ID,
                "table_id": "Budget",
                "columns": json.dumps([{"id": "name", "type": "Text", "is_index": False}]),
            },
            files={"file": ("Budget.csv", b"name\nAlice", "text/csv")},
            headers=_headers(config),
        )

    assert response.status_code == 200
    assert import_service.return_value.import_table.call_args.kwargs["table_id"] == f"Budget_{DOC_ID}"


def test_import_with_invalid_doc_id_is_refused(client, config):
    with patch(f"{ROUTER}.ImportService") as import_service:
        response = client.post(
            "grist-to-superset/api/v3/import/table",
            data={"doc_id": "cKjL2zrDMMRw", "table_id": "Budget", "columns": "[]"},
            files={"file": ("Budget.csv", b"name\nAlice", "text/csv")},
            headers=_headers(config),
        )

    assert response.status_code == 400
    import_service.assert_not_called()


def test_link_creates_the_dataset_of_the_published_table(client, config):
    superset = MagicMock()
    superset.get_user_id_by_username.return_value = 157
    superset.get_or_create_dataset.return_value = 42
    with patch(f"{ROUTER}.SupersetApiService", return_value=superset):
        response = client.post(
            "grist-to-superset/api/v3/link-superset",
            data={"doc_id": DOC_ID, "table_id": "Budget"},
            headers=_headers(config),
        )

    assert response.status_code == 200
    assert superset.get_or_create_dataset.call_args.kwargs["table_name"] == f"Budget_{DOC_ID}"


def test_link_with_too_long_name_is_refused_before_superset(client, config):
    with patch(f"{ROUTER}.SupersetApiService") as superset:
        response = client.post(
            "grist-to-superset/api/v3/link-superset",
            data={"doc_id": DOC_ID, "table_id": "T" * 41},
            headers=_headers(config),
        )

    assert response.status_code == 400
    superset.assert_not_called()
