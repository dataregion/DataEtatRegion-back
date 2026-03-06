from __future__ import annotations

from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from batches.database import init_persistence_module, session_scope
from batches.grist import make_grist_api_service
from prefect import flow, get_run_logger, task
from prefect.cache_policies import NO_CACHE

init_persistence_module()

from models import Base  # noqa: E402
from models.entities.common.SyncedWithGrist import _SyncedWithGrist  # noqa: E402
from models.entities.refs import SynchroGrist  # noqa: E402, F401 — import refs pour enregistrer tous les modèles
from sqlalchemy import insert, select, update  # noqa: E402


def _get_model_by_tablename(tablename: str) -> type:
    for cls in Base.registry._class_registry.values():
        if hasattr(cls, "__tablename__") and cls.__tablename__ == tablename:
            return cls
    raise RuntimeError(f"Aucun modèle SQLAlchemy trouvé pour la table '{tablename}'.")


@task(cache_policy=NO_CACHE)
def validate_model_task(referentiel: str) -> None:
    """Vérifie que le modèle existe, hérite de _SyncedWithGrist et possède une colonne 'code'."""
    logger = get_run_logger()
    model = _get_model_by_tablename(referentiel)
    if not issubclass(model, _SyncedWithGrist):
        raise RuntimeError(f"Le modèle '{referentiel}' n'hérite pas de _SyncedWithGrist.")
    if not hasattr(model, "code"):
        raise RuntimeError(f"Le modèle '{referentiel}' ne possède pas de colonne 'code'.")
    logger.info(f"[GRIST][VALIDATE] Modèle valide : {referentiel}")


@task(cache_policy=NO_CACHE)
def init_synchro_config_task(referentiel: str, doc_id: str, table_id: str) -> dict[str, Any]:
    """Crée ou récupère l'entrée SynchroGrist pour ce référentiel."""
    logger = get_run_logger()
    with session_scope() as session:
        stmt = select(SynchroGrist).where(SynchroGrist.dataetat_table_name == referentiel)
        synchro_grist = session.execute(stmt).scalar_one_or_none()
        if synchro_grist is None:
            synchro_grist = SynchroGrist(
                grist_doc_id=doc_id,
                grist_table_id=table_id,
                dataetat_table_name=referentiel,
            )
            session.add(synchro_grist)
            session.flush()
            logger.info(f"[GRIST][INIT] Entrée SynchroGrist créée pour '{referentiel}'")
        else:
            logger.info(f"[GRIST][INIT] Entrée SynchroGrist existante pour '{referentiel}' (id={synchro_grist.id})")
        # Lire l'id avant l'expiration post-commit
        synchro_id = synchro_grist.id
    return {"synchro_grist_id": synchro_id, "dataetat_table_name": referentiel}


@task(cache_policy=NO_CACHE)
def fetch_grist_records_task(doc_id: str, table_id: str, token: str) -> list[dict[str, Any]]:
    """Récupère les enregistrements depuis l'API Grist."""
    logger = get_run_logger()
    grist_api = make_grist_api_service(token)
    records = grist_api.get_records_of_table(doc_id, table_id)
    logger.info(f"[GRIST][FETCH] {len(records)} enregistrements récupérés depuis Grist")
    return [{"id": r.id, "fields": r.fields} for r in records]


@task(cache_policy=NO_CACHE)
def validate_grist_data_task(records: list[dict[str, Any]], referentiel: str) -> None:
    """Vérifie que les données Grist sont cohérentes avec le modèle SQL."""
    logger = get_run_logger()
    if not records:
        raise RuntimeError(f"[GRIST][VALIDATE] Aucun enregistrement reçu de Grist pour '{referentiel}'.")
    first_fields = records[0]["fields"]
    if "code" not in first_fields:
        raise RuntimeError("La colonne 'code' est absente de la table Grist.")
    model = _get_model_by_tablename(referentiel)
    for col in first_fields.keys():
        if col in ("id", "created_at"):
            raise RuntimeError(f"Nom de colonne interdit dans Grist : '{col}'")
        if not hasattr(model, col):
            raise RuntimeError(f"La colonne Grist '{col}' n'existe pas dans la table '{referentiel}'")
    logger.info(f"[GRIST][VALIDATE] Données Grist valides ({len(records)} enregistrements)")


@task(cache_policy=NO_CACHE)
def sync_batch_task(
    batch: list[dict[str, Any]],
    synchro_meta: dict[str, Any],
    referentiel: str,
) -> dict[str, int]:
    """UPSERT d'un batch de records Grist dans la table de référentiel."""
    logger = get_run_logger()
    model = _get_model_by_tablename(referentiel)
    synchro_grist_id = synchro_meta["synchro_grist_id"]
    now = datetime.now(ZoneInfo("Europe/Paris"))
    inserted = 0
    updated = 0
    with session_scope() as session:
        for record in batch:
            grist_row_id = record["id"]
            fields = dict(record["fields"])
            stmt_select = select(model).where(model.grist_row_id == grist_row_id)  # type: ignore[attr-defined]
            existing = session.execute(stmt_select).scalar_one_or_none()
            if existing is None:
                fields["synchro_grist_id"] = synchro_grist_id
                fields["grist_row_id"] = grist_row_id
                fields["created_at"] = now
                fields["updated_at"] = now
                session.execute(insert(model).values(**fields))
                inserted += 1
                logger.info(f"[GRIST][SYNC] INSERT {referentiel} (grist_row_id={grist_row_id})")
            else:
                fields["updated_at"] = now
                session.execute(
                    update(model)  # type: ignore[arg-type]
                    .where(
                        model.synchro_grist_id == synchro_grist_id,  # type: ignore[attr-defined]
                        model.grist_row_id == grist_row_id,  # type: ignore[attr-defined]
                    )
                    .values(**fields)
                )
                updated += 1
                logger.info(f"[GRIST][SYNC] UPDATE {referentiel} (grist_row_id={grist_row_id})")
    return {"inserted": inserted, "updated": updated}


@task(cache_policy=NO_CACHE)
def soft_delete_missing_task(
    referentiel: str,
    synchro_meta: dict[str, Any],
    all_grist_ids: list[int],
) -> int:
    """Marque is_deleted=True pour les entrées absentes de Grist."""
    logger = get_run_logger()
    model = _get_model_by_tablename(referentiel)
    synchro_grist_id = synchro_meta["synchro_grist_id"]
    now = datetime.now(ZoneInfo("Europe/Paris"))
    count = 0
    with session_scope() as session:
        stmt = select(model).where(  # type: ignore[arg-type]
            model.synchro_grist_id == synchro_grist_id,  # type: ignore[attr-defined]
            model.grist_row_id.notin_(all_grist_ids),  # type: ignore[attr-defined]
            model.is_deleted == False,  # noqa: E712
        )
        rows_to_delete = session.execute(stmt).scalars().all()
        for row in rows_to_delete:
            session.execute(
                update(model)  # type: ignore[arg-type]
                .where(model.id == row.id)  # type: ignore[attr-defined]
                .values(is_deleted=True, updated_at=now)
            )
            count += 1
            logger.info(f"[GRIST][SYNC] SOFT DELETE {referentiel} (id={row.id})")
    return count


@flow
def sync_referentiel_grist_flow(
    referentiel: str,
    doc_id: str,
    table_id: str,
    token: str,
    batch_size: int = 100,
):
    """
    Synchronise un référentiel de la base de données avec une table Grist.

    Args:
        referentiel: Nom de la table SQL du référentiel (ex: 'ref_centre_couts').
        doc_id: Identifiant du document Grist.
        table_id: Identifiant de la table Grist.
        token: Token d'accès à l'API Grist.
        batch_size: Taille des batches de synchronisation (défaut: 100).
    """
    logger = get_run_logger()
    logger.info(f"[GRIST] Démarrage sync '{referentiel}' (doc={doc_id}, table={table_id})")

    validate_model_task(referentiel)
    synchro_meta = init_synchro_config_task(referentiel, doc_id, table_id)

    records = fetch_grist_records_task(doc_id, table_id, token)
    validate_grist_data_task(records, referentiel)

    all_grist_ids = [r["id"] for r in records]

    # Soumettre les batches en parallèle
    futures = []
    for i in range(0, len(records), batch_size):
        batch = records[i : i + batch_size]
        futures.append(sync_batch_task.submit(batch, synchro_meta, referentiel))

    results = [f.result() for f in futures]
    total_inserted = sum(r["inserted"] for r in results)
    total_updated = sum(r["updated"] for r in results)
    logger.info(f"[GRIST] Batches terminés : {total_inserted} insérés, {total_updated} mis à jour")

    deleted_count = soft_delete_missing_task(referentiel, synchro_meta, all_grist_ids)
    logger.info(f"[GRIST] Soft delete : {deleted_count} lignes marquées supprimées")
    logger.info(f"[GRIST] Sync terminée pour '{referentiel}'")


if __name__ == "__main__":
    sync_referentiel_grist_flow(
        referentiel="ref_centre_couts",
        doc_id="<docId>",
        table_id="<tableId>",
        token="<token>",
    )
