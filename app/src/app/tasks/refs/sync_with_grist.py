from datetime import datetime
import logging
from typing import List
from zoneinfo import ZoneInfo

from models.entities.common.SyncedWithGrist import _SyncedWithGrist
from sqlalchemy import insert, select, update

from gristcli.models import Record
from models import Base
from models.entities.refs.SynchroGrist import SynchroGrist

from app import db, celeryapp
from app.clients.grist.factory import make_grist_api_client


logger = logging.getLogger()

celery = celeryapp.celery


def _get_model_by_tablename(tablename):
    for cls in Base.registry._class_registry.values():
        if hasattr(cls, "__tablename__") and cls.__tablename__ == tablename:
            return cls
    return None


def _get_sync_config(doc_id: str, table_id: str, table_name: str):
    stmt = select(SynchroGrist).where(
        SynchroGrist.grist_doc_id == doc_id,
        SynchroGrist.grist_table_id == table_id,
        SynchroGrist.dataetat_table_name == table_name,
    )
    synchro_grist: SynchroGrist = db.session.execute(stmt).scalar_one_or_none()
    if synchro_grist is None:
        raise RuntimeError("No synchro for Grist defined.")

    model = _get_model_by_tablename(table_name)
    if model is None:
        logger.error("[GRIST][VALIDATION] Can't find model to synchronize")
        raise RuntimeError("Can't find model to synchronize.")
    if not issubclass(model, _SyncedWithGrist):
        logger.error("[GRIST][VALIDATION] Can't apply Grist synchronization")
        raise RuntimeError("Can't apply Grist synchronization.")
    return model, synchro_grist


@celery.task(name="init_referentiels_with_grist", bind=True)
def init_referentiels_from_grist(self, token: str, doc_id: str, table_id: str, table_name: str):
    try:
        logger.info("[GRIST][INIT] Start Call init-grist-to-db")
        grist_api = make_grist_api_client(token)

        model, synchro_grist = _get_sync_config(doc_id, table_id, table_name)

        referentiels = list(db.session.execute(select(model)).scalars().all())
        records: List[Record] = grist_api.get_records_of_table(synchro_grist.grist_doc_id, synchro_grist.grist_table_id)

        # Vérification de la présence de la colonne code dans la table Grist
        first = records[0] if len(records) > 0 else None
        if first is not None and "code" not in first.fields.keys():
            raise Exception("Colonne `code` non présente dans la table Grist")

        # Synchro des colonnes faisant le lien avec la table Grist
        now = datetime.now(ZoneInfo("Europe/Paris"))
        for r in referentiels:
            match = next((t for t in records if str(r.code) == str(t.fields.get("code"))), None)
            stmt = (
                update(model)
                .where(model.id == r.id)
                .values(
                    synchro_grist_id=synchro_grist.id,
                    grist_row_id=match.id if match is not None else None,
                    is_deleted=(match is None),
                    updated_at=now,
                )
            )
            db.session.execute(stmt)
            logging.info(f"[GRIST][INIT] UPDATE {table_name} : {r.id}")

        db.session.commit()
        logger.info("[GRIST][INIT] End Call init-grist-to-db")
    except Exception as e:
        logger.exception(f"[GRIST][INIT] Error lors de la synchro du référentiel {table_name}.")
        raise e


@celery.task(name="sync_referentiels_with_grist", bind=True)
def sync_referentiels_from_grist(self, token: str, doc_id: str, table_id: str, table_name: str):
    try:
        logger.info("[GRIST][SYNC] Start Call sync-grist-to-db")
        grist_api = make_grist_api_client(token)

        model, synchro_grist = _get_sync_config(doc_id, table_id, table_name)

        referentiels: list[_SyncedWithGrist] = list(db.session.execute(select(model)).scalars().all())
        records: List[Record] = grist_api.get_records_of_table(synchro_grist.grist_doc_id, synchro_grist.grist_table_id)

        # Check correspondance colonnes grist et DB
        first = records[0] if len(records) > 0 else None
        if first is not None:
            for col in first.fields.keys():
                if col == "id" and col == "created_at":
                    raise Exception(f"Nom de colonne interdit : `{col}`")
                if not hasattr(model, col):
                    raise Exception(f"La colonne Grist `{col}` n'existe pas dans la table `{table_name}`")

        # Traitement de chaque ligne de la table grist
        now = datetime.now(ZoneInfo("Europe/Paris"))
        for r in records:
            stmt = None
            match = next((t for t in referentiels if t.grist_row_id == r.id), None)

            fields = r.fields
            if match is None:
                fields["synchro_grist_id"] = synchro_grist.id
                fields["grist_row_id"] = r.id
                fields["created_at"] = now
                fields["updated_at"] = now
                stmt = insert(model).values(**fields)
                logging.info(f"[GRIST][SYNC] INSERT {table_name} : {r.id}")
                db.session.execute(stmt)
                continue

            fields["updated_at"] = now
            referentiels.remove(match)
            stmt = (
                update(model)
                .where(model.synchro_grist_id == synchro_grist.id, model.grist_row_id == r.id)
                .values(**fields)
            )
            logging.info(f"[GRIST][SYNC] UPDATE {table_name} : {r.id}")
            db.session.execute(stmt)

        if len(referentiels) > 0:
            for t in referentiels:
                stmt = update(model).where(model.id == t.id).values(is_deleted=True, updated_at=now)
                logging.info(f"[GRIST][SYNC] SOFT DELETE {table_name} : {t.grist_row_id}")
                db.session.execute(stmt)

        db.session.commit()
        logger.info("[GRIST][SYNC] End Call sync-grist-to-db")
    except Exception as e:
        logger.exception(f"[GRIST][SYNC] Error lors de la synchro du référentiel {table_name}.")
        raise e
