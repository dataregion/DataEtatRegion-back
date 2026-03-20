import base64
from pathlib import Path

from fastapi.testclient import TestClient

from apis.apps.budget.api import app as budget_app
from apis.database import session_audit_scope
from models.entities.audit.AuditInsertFinancialTasks import AuditInsertFinancialTasks


def _encode_tus_metadata(metadata: dict[str, str]) -> str:
    return ",".join(f"{key} {base64.b64encode(value.encode()).decode()}" for key, value in metadata.items())


def _upload_file(
    client: TestClient,
    *,
    filename: str,
    content: bytes,
    session_token: str,
    upload_type: str,
    year: int,
    total_ae_files: int,
    total_cp_files: int,
) -> str:
    create_response = client.post(
        "/import",
        headers={
            "Tus-Resumable": "1.0.0",
            "Upload-Length": str(len(content)),
            "Upload-Metadata": _encode_tus_metadata(
                {
                    "filename": filename,
                    "filetype": "text/csv",
                    "session_token": session_token,
                    "year": str(year),
                    "uploadType": upload_type,
                    "total_ae_files": str(total_ae_files),
                    "total_cp_files": str(total_cp_files),
                }
            ),
        },
    )

    assert create_response.status_code == 201, create_response.text
    upload_url = create_response.headers["location"]

    patch_response = client.patch(
        upload_url,
        content=content,
        headers={
            "Tus-Resumable": "1.0.0",
            "Upload-Offset": "0",
            "Content-Type": "application/offset+octet-stream",
        },
    )

    assert patch_response.status_code == 204, patch_response.text
    assert patch_response.headers["upload-offset"] == str(len(content))
    return upload_url


def test_import_process_uploads_ae_and_cp_idempotency(test_db, admin_budget_persona, keycloak_validator_patch_fn):

    session_token = None
    keycloak_validator_patch_fn(admin_budget_persona)

    with TestClient(budget_app) as client:
        initialize_response = client.post(
            "/import/session/initialize",
            json={
                "total_ae_files": 1,
                "total_cp_files": 1,
                "year": 2025,
            },
        )

        assert initialize_response.status_code == 201, initialize_response.text
        session_token = initialize_response.json()["session_token"]

        ae_content = b"programme,montant\nAE-1,100\n"
        cp_content = b"programme,montant\nCP-1,200\n"

        for _ in range(2):  # Upload the same files twice to test idempotency
            _upload_file(
                client,
                filename="ae.csv",
                content=ae_content,
                session_token=session_token,
                upload_type="financial-ae",
                year=2025,
                total_ae_files=1,
                total_cp_files=1,
            )
        for _ in range(2):  # Upload the same files twice to test idempotency
            _upload_file(
                client,
                filename="cp.csv",
                content=cp_content,
                session_token=session_token,
                upload_type="financial-cp",
                year=2025,
                total_ae_files=1,
                total_cp_files=1,
            )

        check_response = client.get(f"/import/session/{session_token}")
        assert check_response.status_code == 200, check_response.text

    with session_audit_scope() as session:
        audit_row = session.query(AuditInsertFinancialTasks).filter_by(session_token=session_token).one()

        assert audit_row.fichier_ae.endswith("_AE_2025.csv")
        assert audit_row.fichier_cp.endswith("_CP_2025.csv")
        assert Path(audit_row.fichier_ae).exists()
        assert Path(audit_row.fichier_cp).exists()
        assert audit_row.username == "test@example.com"
        assert audit_row.annee == 2025

        _1 = Path(audit_row.fichier_ae)
        _2 = Path(audit_row.fichier_cp)


def test_import_process_uploads_ae_and_cp_files_with_fastapi_testclient(
    test_db, admin_budget_persona, keycloak_validator_patch_fn
):
    session_token = None

    keycloak_validator_patch_fn(admin_budget_persona)

    with TestClient(budget_app) as client:
        initialize_response = client.post(
            "/import/session/initialize",
            json={
                "total_ae_files": 1,
                "total_cp_files": 1,
                "year": 2025,
            },
        )

        assert initialize_response.status_code == 201, initialize_response.text
        session_token = initialize_response.json()["session_token"]

        ae_content = b"programme,montant\nAE-1,100\n"
        cp_content = b"programme,montant\nCP-1,200\n"

        _upload_file(
            client,
            filename="ae.csv",
            content=ae_content,
            session_token=session_token,
            upload_type="financial-ae",
            year=2025,
            total_ae_files=1,
            total_cp_files=1,
        )
        _upload_file(
            client,
            filename="cp.csv",
            content=cp_content,
            session_token=session_token,
            upload_type="financial-cp",
            year=2025,
            total_ae_files=1,
            total_cp_files=1,
        )

        check_response = client.get(f"/import/session/{session_token}")
        assert check_response.status_code == 200, check_response.text

    with session_audit_scope() as session:
        audit_row = session.query(AuditInsertFinancialTasks).filter_by(session_token=session_token).one()

        assert audit_row.fichier_ae.endswith("_AE_2025.csv")
        assert audit_row.fichier_cp.endswith("_CP_2025.csv")
        assert Path(audit_row.fichier_ae).exists()
        assert Path(audit_row.fichier_cp).exists()
        assert audit_row.username == "test@example.com"
        assert audit_row.annee == 2025

        _1 = Path(audit_row.fichier_ae)
        _2 = Path(audit_row.fichier_cp)
