from __future__ import annotations

from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from batches.database import init_persistence_module, session_scope
from batches.config.current import get_config
from batches.grist import make_grist_api_service
from prefect import flow, get_run_logger, task
from prefect.cache_policies import NO_CACHE

init_persistence_module()

from models import Base  # noqa: E402
from models.entities.common.SyncedWithGrist import _SyncedWithGrist  # noqa: E402
from models.entities.refs import SynchroGrist  # noqa: E402, F401 — import refs pour enregistrer tous les modèles
from sqlalchemy import select, update  # noqa: E402
from sqlalchemy.dialects.postgresql import insert  # noqa: E402


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
            logger.info(
                f"[GRIST][INIT] Entrée SynchroGrist existante pour '{referentiel}' (doc_id={synchro_grist.grist_doc_id})"
            )
        # Lire l'id et les infos Grist avant l'expiration post-commit
        synchro_id = synchro_grist.id
        grist_doc = getattr(synchro_grist, "grist_doc_id", None)
        grist_table = getattr(synchro_grist, "grist_table_id", None)
    return {
        "synchro_grist_id": synchro_id,
        "dataetat_table_name": referentiel,
        "grist_doc_id": grist_doc,
        "grist_table_id": grist_table,
    }


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

    with session_scope() as session:
        # Récupérer les codes existants pour compter inserted vs updated
        batch_codes = [record["fields"]["code"] for record in batch if "code" in record["fields"]]
        stmt_existing = select(model.code).where(model.code.in_(batch_codes))  # type: ignore[attr-defined]
        existing_codes = set(session.execute(stmt_existing).scalars().all())

        inserted = 0
        updated = 0

        for record in batch:
            grist_row_id = record["id"]
            fields = dict(record["fields"])

            # Préparer les valeurs pour l'UPSERT
            values = {
                **fields,
                "synchro_grist_id": synchro_grist_id,
                "grist_row_id": grist_row_id,
                "created_at": now,
                "updated_at": now,
            }

            # Valeurs à mettre à jour en cas de conflit (tous les champs sauf created_at)
            update_values = {
                **fields,
                "synchro_grist_id": synchro_grist_id,
                "grist_row_id": grist_row_id,
                "updated_at": now,
            }

            # UPSERT avec ON CONFLICT DO UPDATE sur la colonne 'code'
            stmt = insert(model).values(**values)
            stmt = stmt.on_conflict_do_update(
                index_elements=["code"],  # Colonne avec contrainte UNIQUE
                set_=update_values,
            )
            session.execute(stmt)

            # Compter inserted vs updated
            if fields.get("code") in existing_codes:
                updated += 1
                logger.info(
                    f"[GRIST][SYNC] UPDATE {referentiel} (code={fields.get('code')}, grist_row_id={grist_row_id})"
                )
            else:
                inserted += 1
                logger.info(
                    f"[GRIST][SYNC] INSERT {referentiel} (code={fields.get('code')}, grist_row_id={grist_row_id})"
                )

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
    token: str,
    grist_doc_id: str | None = None,
    grist_table_id: str | None = None,
    batch_size: int = 100,
):
    """
    Synchronise un référentiel de la base de données avec une table Grist.

    Args:
        referentiel: Nom de la table SQL du référentiel (ex: 'ref_centre_couts').
        grist_doc_id: Identifiant du document Grist.
        grist_table_id: Identifiant de la table Grist.
        token: Token d'accès à l'API Grist.
        batch_size: Taille des batches de synchronisation (défaut: 100).
    """
    logger = get_run_logger()
    logger.info(f"[GRIST] Démarrage sync '{referentiel}' (doc={grist_doc_id}, table={grist_table_id})")

    validate_model_task(referentiel)

    # Initialiser ou récupérer la config de synchronisation. Si `grist_doc_id`/`grist_table_id`
    # ne sont pas fournis, `init_synchro_config_task` retournera les valeurs existantes en base.
    synchro_meta = init_synchro_config_task(referentiel, grist_doc_id, grist_table_id)
    grist_doc_id = synchro_meta.get("grist_doc_id")
    grist_table_id = synchro_meta.get("grist_table_id")

    if not grist_doc_id or not grist_table_id:
        raise RuntimeError("grist_doc_id et grist_table_id sont requis pour récupérer les enregistrements Grist")

    records = fetch_grist_records_task(grist_doc_id, grist_table_id, token)
    validate_grist_data_task(records, referentiel)

    all_grist_ids = [r["id"] for r in records]

    # Traitement des batches avec parallélisme limité pour ne pas saturer le pool DB
    # Lire la configuration si disponible (défaut 3)
    max_concurrent = get_config().max_concurrent
    total_inserted = 0
    total_updated = 0
    all_batches = [records[i : i + batch_size] for i in range(0, len(records), batch_size)]
    total_batches = len(all_batches)

    for group_start in range(0, total_batches, max_concurrent):
        group = all_batches[group_start : group_start + max_concurrent]
        group_num_start = group_start + 1
        group_num_end = min(group_start + max_concurrent, total_batches)
        logger.info(f"[GRIST] Lancement batches {group_num_start}-{group_num_end}/{total_batches}")

        futures = [sync_batch_task.submit(batch, synchro_meta, referentiel) for batch in group]
        for f in futures:
            result = f.result()
            total_inserted += result["inserted"]
            total_updated += result["updated"]

    logger.info(f"[GRIST] Batches terminés : {total_inserted} insérés, {total_updated} mis à jour")

    deleted_count = soft_delete_missing_task(referentiel, synchro_meta, all_grist_ids)
    logger.info(f"[GRIST] Soft delete : {deleted_count} lignes marquées supprimées")
    logger.info(f"[GRIST] Sync terminée pour '{referentiel}'")


if __name__ == "__main__":
    sync_referentiel_grist_flow(
        referentiel="<ref>",
        token="<token>",
        grist_doc_id=None,
        grist_table_id=None,
        batch_size=1000,
    )
