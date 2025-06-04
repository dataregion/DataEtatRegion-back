from http import HTTPStatus
import logging
from typing import List
from app import db, celeryapp
from app.clients.grist.factory import make_grist_api_client, make_or_get_grist_database_client, make_or_get_grist_scim_client
from flask import current_app
from gristcli.gristservices.users_grist_service import UserGristDatabaseService, UserScimService
from gristcli.models import Record, Table
from models.entities.refs import Theme
from sqlalchemy import insert, select, update


logger = logging.getLogger()

celery = celeryapp.celery


@celery.task(name="sync_referentiels_with_grist", bind=True)
def sync_referentiels_from_grist(self, user_mail: str, docId: str):
    userService: UserGristDatabaseService = make_or_get_grist_database_client()
    userScimService: UserScimService = make_or_get_grist_scim_client()
    # check user exist
    logger.info(f"[GRIST] Start Call sync-grist-to-db for user {user_mail}")
    user = userScimService.search_user_by_username(user_mail)
    if user is None:
        logger.debug("[GRIST] No user.")
        return

    # Recup token
    logger.debug(f"[GRIST] Get Api key for user {user.username}")
    token = userService.get_or_create_api_token(user.user_id)
    grist_api = make_grist_api_client(token)
    logger.debug("[GRIST] Retrieve token sucess")

    # Fetch data from grist
    tables : List[Table] = grist_api.get_tables_of_doc(docId)
    for t in tables:

        # On ne gère que les thèmes
        if t.id == "Themes":
            themes = list(db.session.execute(select(Theme)).scalars().all())
            records: List[Record] = grist_api.get_records_of_table(docId, t.id)

            # Traitement de chaque ligne de la table grist
            for r in records:
                stmt = None
                match: Theme | None = next((t for t in themes if t.grist_row_id == r.id), None)
                if match is None:
                    stmt = insert(Theme).values(grist_row_id=r.id, label=r.fields["libelle"])
                    db.session.execute(stmt)
                    continue

                themes.remove(match)
                if match.label != r.fields["libelle"]:
                    stmt = update(Theme).where(Theme.grist_row_id == r.id).values(label=r.fields["libelle"])
                    db.session.execute(stmt)

            if len(themes) > 0:
                for t in themes:
                    stmt = update(Theme).where(Theme.id == t.id).values(is_deleted=True)
                    db.session.execute(stmt)
            
    db.session.commit()
    logger.info(f"[GRIST] End Call sync-grist-to-db for user {user.username}")