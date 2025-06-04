import logging
from typing import List
from app import db, celeryapp
from app.clients.grist.factory import make_grist_api_client
from gristcli.models import Record
from models import Base
from models.entities.refs.SynchroGrist import SynchroGrist
from sqlalchemy import insert, select, update


logger = logging.getLogger()

celery = celeryapp.celery


def get_model_by_tablename(tablename):
    for cls in Base.registry._class_registry.values():
        if hasattr(cls, "__tablename__") and cls.__tablename__ == tablename:
            return cls
    return None


@celery.task(name="sync_referentiels_with_grist", bind=True)
def sync_referentiels_from_grist(self, token: str, doc_id: str, table_id: str, table_name: str):
    try:
        logger.info("[GRIST][SYNC] Start Call sync-grist-to-db")
        grist_api = make_grist_api_client(token)

        stmt = select(SynchroGrist).where(
            SynchroGrist.grist_doc_id == doc_id,
            SynchroGrist.grist_table_id == table_id,
            SynchroGrist.grist_table_name == table_name,
        )
        sg: SynchroGrist = db.session.execute(stmt).scalar_one_or_none()
        if sg is None:
            raise Exception("No synchro for Grist defined.")

        model = get_model_by_tablename(table_name)
        if model is None:
            raise Exception("Can't find model to synchronize.")

        referentiels = list(db.session.execute(select(model)).scalars().all())
        records: List[Record] = grist_api.get_records_of_table(sg.grist_doc_id, sg.grist_table_id)

        # Traitement de chaque ligne de la table grist
        for r in records:
            stmt = None
            match = next((t for t in referentiels if t.grist_row_id == r.id), None)
            if match is None:
                stmt = insert(model).values(synchro_grist_id=sg.id, grist_row_id=r.id, label=r.fields["libelle"])
                logging.info(f"[GRIST][SYNC] INSERT Nouveau thème : {r.fields["libelle"]}")
                db.session.execute(stmt)
                continue

            referentiels.remove(match)
            if match.label != r.fields["libelle"]:
                stmt = (
                    update(model)
                    .where(model.synchro_grist_id == sg.id, model.grist_row_id == r.id)
                    .values(label=r.fields["libelle"])
                )
                logging.info(f"[GRIST][SYNC] UPDATE Thème {r.id} : {r.fields["libelle"]}")
                db.session.execute(stmt)

        if len(referentiels) > 0:
            for t in referentiels:
                stmt = update(model).where(model.id == t.id).values(is_deleted=True)
                logging.info(f"[GRIST][SYNC] SOFT DELETE Thème {t.grist_row_id}")
                db.session.execute(stmt)

        db.session.commit()
        logger.info("[GRIST][SYNC] End Call sync-grist-to-db")
    except Exception as e:
        logger.exception(f"[GRIST][SYNC] Error lors de la synchro du référentiel {table_name}.")
        raise e
