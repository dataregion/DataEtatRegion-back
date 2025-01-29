from unittest.mock import patch

from app.tasks.files.file_task import delayed_inserts
from models.entities.audit.AuditInsertFinancialTasks import AuditInsertFinancialTasks
from models.entities.audit.AuditUpdateData import AuditUpdateData
import pytest


@pytest.fixture(scope="function")
def insert_audit_region(database):
    audit = AuditInsertFinancialTasks(
        fichier_ae="/path/ae",  # type: ignore
        fichier_cp="/path/cp",  # type: ignore
        source_region="53",  # type: ignore
        annee=2024,  # type: ignore
        username="username",  # type: ignore
        application_clientid="client_id",  # type: ignore
    )
    database.session.add(audit)
    database.session.commit()
    yield audit
    database.session.execute(database.delete(AuditUpdateData))
    database.session.commit()


@pytest.fixture(scope="function")
def insert_audit_national(database):
    audit = AuditInsertFinancialTasks(
        fichier_ae="/path/ae",  # type: ignore
        fichier_cp="/path/cp",  # type: ignore
        source_region="NATIONAL",  # type: ignore
        annee=0,  # type: ignore
        username="username",  # type: ignore
        application_clientid="client_id",  # type: ignore
    )
    database.session.add(audit)
    database.session.commit()
    yield audit
    database.session.execute(database.delete(AuditUpdateData))
    database.session.commit()


def test_delayed_insert_region(insert_audit_region, database, session):
    # DO
    with (
        patch("app.tasks.files.file_task.read_csv_and_import_ae_cp.delay") as mock_task,
        patch("app.tasks.files.file_task.delete_cp_annee_region") as mock_delete_cp,
        patch("app.tasks.files.file_task.delete_ae_no_cp_annee_region") as mock_delete_ae,
    ):
        delayed_inserts()

        # Vérification que les fonctions de suppression ont bien été appelées avec les bons arguments
        mock_delete_cp.assert_called_once_with(2024, "53")
        mock_delete_ae.assert_called_once_with(2024, "53")

        # Vérification que la tâche Celery a été appelée une fois avec les bons arguments
        mock_task.assert_called_once_with(
            "/path/ae",
            "/path/cp",
            '{"sep": ",", "skiprows": 7}',
            source_region="53",
            annee=2024,
        )

    result = session.execute(database.select(AuditUpdateData))
    audits = result.scalars().all()

    assert len(audits) == 2  # Une ligne pour AE et une pour CP
    assert all(aud.source_region == "53" for aud in audits)
    assert all(aud.application_clientid == "client_id" for aud in audits)
    assert all(aud.username == "username" for aud in audits)


def test_delayed_insert_national(insert_audit_national, database, session):
    """Teste que delayed_inserts ne supprime pas de données et ne déclenche pas d'import pour la région NATIONAL."""

    with (
        patch("app.tasks.files.file_task.read_csv_and_import_ae_cp.delay") as mock_task,
        patch("app.tasks.files.file_task.delete_cp_annee_region") as mock_delete_cp,
        patch("app.tasks.files.file_task.delete_ae_no_cp_annee_region") as mock_delete_ae,
        patch("app.tasks.files.file_task.read_csv_and_import_fichier_nat_ae_cp.delay") as mock_import_nationals,
    ):

        # Exécution de la fonction testée
        delayed_inserts()

        # Vérifier que les fonctions de suppression ae cp ne sont PAS appelées
        mock_delete_cp.assert_not_called()
        mock_delete_ae.assert_not_called()

        # Vérifier que la tâche Celery d'import region n'est PAS déclenchée
        mock_task.assert_not_called()

        mock_import_nationals.assert_called_once()

    # Vérifier qu'aucune entrée AuditUpdateData n'a été insérée
    audits = session.execute(database.select(AuditUpdateData)).scalars().all()

    assert len(audits) == 2  # Une ligne pour AE et une pour CP
    assert all(aud.source_region == "NATIONAL" for aud in audits)
    assert all(aud.application_clientid == "client_id" for aud in audits)
    assert all(aud.username == "username" for aud in audits)
