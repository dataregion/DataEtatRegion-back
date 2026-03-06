"""Tests unitaires pour le flow sync_referentiel_grist."""

import logging
from typing import Any
from unittest.mock import patch

import pytest
from sqlalchemy import select, delete

from models.entities.refs import CentreCouts, SynchroGrist


# ---------------------------------------------------------------------------
# Tests validate_model_task
# ---------------------------------------------------------------------------


def test_validate_model_task_ok(caplog: Any):
    from batches.prefect.sync_referentiel_grist import validate_model_task

    caplog.set_level(logging.INFO)
    # ref_centre_couts hérite de _SyncedWithGrist et possède 'code'
    validate_model_task("ref_centre_couts")
    assert "[GRIST][VALIDATE] Modèle valide : ref_centre_couts" in caplog.messages


def test_validate_model_task_unknown_table():
    from batches.prefect.sync_referentiel_grist import validate_model_task

    with pytest.raises(RuntimeError, match="Aucun modèle SQLAlchemy trouvé"):
        validate_model_task("table_qui_nexiste_pas")


def test_validate_model_task_not_synced_with_grist():
    """Un modèle sans _SyncedWithGrist doit lever une RuntimeError."""
    from batches.prefect.sync_referentiel_grist import validate_model_task

    # On simule un modèle sans _SyncedWithGrist via un patch sur _get_model_by_tablename
    class _FakeModel:
        pass

    with patch(
        "batches.prefect.sync_referentiel_grist._get_model_by_tablename",
        return_value=_FakeModel,
    ):
        with pytest.raises(RuntimeError, match="n'hérite pas de _SyncedWithGrist"):
            validate_model_task("ref_fake")


# ---------------------------------------------------------------------------
# Tests validate_grist_data_task
# ---------------------------------------------------------------------------


def test_validate_grist_data_task_ok():
    from batches.prefect.sync_referentiel_grist import validate_grist_data_task

    records = [{"id": 1, "fields": {"code": "A001", "label": "Test"}}]
    validate_grist_data_task(records, "ref_centre_couts")


def test_validate_grist_data_task_empty():
    from batches.prefect.sync_referentiel_grist import validate_grist_data_task

    with pytest.raises(RuntimeError, match="Aucun enregistrement"):
        validate_grist_data_task([], "ref_centre_couts")


def test_validate_grist_data_task_missing_code():
    from batches.prefect.sync_referentiel_grist import validate_grist_data_task

    records = [{"id": 1, "fields": {"label": "Test"}}]
    with pytest.raises(RuntimeError, match="'code' est absente"):
        validate_grist_data_task(records, "ref_centre_couts")


def test_validate_grist_data_task_forbidden_column():
    from batches.prefect.sync_referentiel_grist import validate_grist_data_task

    records = [{"id": 1, "fields": {"code": "A001", "id": 99}}]
    with pytest.raises(RuntimeError, match="colonne interdit"):
        validate_grist_data_task(records, "ref_centre_couts")


def test_validate_grist_data_task_unknown_column():
    from batches.prefect.sync_referentiel_grist import validate_grist_data_task

    records = [{"id": 1, "fields": {"code": "A001", "colonne_inconnue": "valeur"}}]
    with pytest.raises(RuntimeError, match="n'existe pas dans la table"):
        validate_grist_data_task(records, "ref_centre_couts")


# ---------------------------------------------------------------------------
# Tests init_synchro_config_task (avec DB)
# ---------------------------------------------------------------------------


def test_init_synchro_config_task_creates_new(session):  # noqa: F811
    """Quand aucune entrée SynchroGrist n'existe, la tâche doit en créer une."""
    from batches.prefect.sync_referentiel_grist import init_synchro_config_task

    result = init_synchro_config_task("ref_centre_couts", "doc123", "table456")

    assert result["dataetat_table_name"] == "ref_centre_couts"
    assert result["synchro_grist_id"] is not None

    synchro = session.execute(
        select(SynchroGrist).where(SynchroGrist.dataetat_table_name == "ref_centre_couts")
    ).scalar_one_or_none()
    assert synchro is not None
    assert synchro.grist_doc_id == "doc123"
    assert synchro.grist_table_id == "table456"

    # Nettoyage
    session.execute(delete(SynchroGrist).where(SynchroGrist.dataetat_table_name == "ref_centre_couts"))
    session.commit()


def test_init_synchro_config_task_returns_existing(session):  # noqa: F811
    """Quand une entrée SynchroGrist existe déjà, la tâche doit la retourner sans créer de doublon."""
    from batches.prefect.sync_referentiel_grist import init_synchro_config_task

    existing = SynchroGrist(grist_doc_id="docXYZ", grist_table_id="tableXYZ", dataetat_table_name="ref_centre_couts")
    session.add(existing)
    session.commit()
    existing_id = existing.id

    result = init_synchro_config_task("ref_centre_couts", "docXYZ", "tableXYZ")

    assert result["synchro_grist_id"] == existing_id
    count = session.execute(select(SynchroGrist).where(SynchroGrist.dataetat_table_name == "ref_centre_couts")).all()
    assert len(count) == 1

    # Nettoyage
    session.execute(delete(SynchroGrist).where(SynchroGrist.dataetat_table_name == "ref_centre_couts"))
    session.commit()


# ---------------------------------------------------------------------------
# Tests sync_batch_task (avec DB)
# ---------------------------------------------------------------------------


def _create_synchro_grist(session, table_name="ref_centre_couts") -> SynchroGrist:
    synchro = SynchroGrist(grist_doc_id="docTest", grist_table_id="tblTest", dataetat_table_name=table_name)
    session.add(synchro)
    session.commit()
    return synchro


def test_sync_batch_task_insert(session):
    """Un record absent de la DB doit être inséré."""
    from batches.prefect.sync_referentiel_grist import sync_batch_task

    synchro = _create_synchro_grist(session)
    synchro_meta = {"synchro_grist_id": synchro.id}
    batch = [{"id": 42, "fields": {"code": "BG00/C001", "label": "Centre test"}}]

    result = sync_batch_task(batch, synchro_meta, "ref_centre_couts")

    assert result["inserted"] == 1
    assert result["updated"] == 0
    row = session.execute(select(CentreCouts).where(CentreCouts.grist_row_id == 42)).scalar_one_or_none()
    assert row is not None
    assert row.synchro_grist_id == synchro.id

    # Nettoyage
    session.execute(delete(CentreCouts).where(CentreCouts.grist_row_id == 42))
    session.execute(delete(SynchroGrist).where(SynchroGrist.id == synchro.id))
    session.commit()


def test_sync_batch_task_update(session):
    """Un record déjà présent en DB (grist_row_id identique) doit être mis à jour."""
    from batches.prefect.sync_referentiel_grist import sync_batch_task

    synchro = _create_synchro_grist(session)
    existing = CentreCouts(code="BG00/C002", label="Ancien label", grist_row_id=99, synchro_grist_id=synchro.id)
    session.add(existing)
    session.commit()

    synchro_meta = {"synchro_grist_id": synchro.id}
    batch = [{"id": 99, "fields": {"code": "BG00/C002", "label": "Nouveau label"}}]

    result = sync_batch_task(batch, synchro_meta, "ref_centre_couts")

    assert result["inserted"] == 0
    assert result["updated"] == 1
    updated = session.execute(select(CentreCouts).where(CentreCouts.grist_row_id == 99)).scalar_one()
    assert updated.label == "Nouveau label"

    # Nettoyage
    session.execute(delete(CentreCouts).where(CentreCouts.grist_row_id == 99))
    session.execute(delete(SynchroGrist).where(SynchroGrist.id == synchro.id))
    session.commit()


# ---------------------------------------------------------------------------
# Tests soft_delete_missing_task (avec DB)
# ---------------------------------------------------------------------------


def test_soft_delete_missing_task(session):  # noqa: F811
    """Les lignes non présentes dans Grist doivent être marquées is_deleted=True."""
    from batches.prefect.sync_referentiel_grist import soft_delete_missing_task

    synchro = _create_synchro_grist(session)
    # Ligne encore présente dans Grist (grist_row_id=10)
    present = CentreCouts(code="BG00/P001", label="Present", grist_row_id=10, synchro_grist_id=synchro.id)
    # Ligne absente de Grist (grist_row_id=20)
    absent = CentreCouts(code="BG00/A001", label="Absent", grist_row_id=20, synchro_grist_id=synchro.id)
    session.add_all([present, absent])
    session.commit()  # ✅ Commit pour persister les données (visible par toutes les sessions)

    synchro_meta = {"synchro_grist_id": synchro.id}
    # On signale que seul grist_row_id=10 est encore présent
    count = soft_delete_missing_task("ref_centre_couts", synchro_meta, [10])

    assert count == 1
    absent_row = session.execute(select(CentreCouts).where(CentreCouts.grist_row_id == 20)).scalar_one()
    assert absent_row.is_deleted is True
    present_row = session.execute(select(CentreCouts).where(CentreCouts.grist_row_id == 10)).scalar_one()
    assert present_row.is_deleted is False

    # Nettoyage
    ids_to_delete = [present.id, absent.id]
    for row_id in ids_to_delete:
        session.execute(delete(CentreCouts).where(CentreCouts.id == row_id))
    session.execute(delete(SynchroGrist).where(SynchroGrist.id == synchro.id))
    session.commit()
