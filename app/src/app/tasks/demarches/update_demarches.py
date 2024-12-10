import logging
from app.services.demarches.demarches import DemarcheService

from celery import subtask
from app import celeryapp
from app.tasks import limiter_queue


celery = celeryapp.celery
LOGGER = logging.getLogger()


@limiter_queue(queue_name="line")
def _send_subtask_update_demarche(uuid_user: str, token_id: int, demarche_number: int):
    subtask("update_demarche").delay(uuid_user, token_id, demarche_number)


@celery.task(name="update_demarches", bind=True)
def update_demarches(self):
    demarches = DemarcheService.find_to_update()
    LOGGER.info(f"[UPDATE][DEMARCHES] Récupération de {len(demarches)} démarches à réintégrer")
    for d in demarches:
        _send_subtask_update_demarche(d.token.uuid_utilisateur, d.token.id, d.number)


@celery.task(name="update_demarche", bind=True)
def update_demarche(self, uuid_user: str, token_id: int, demarche_number: int):
    demarche = DemarcheService.integrer_demarche(uuid_user, token_id, demarche_number)
    LOGGER.info(f"[UPDATE][DEMARCHE] Démarche {demarche.number} mise à jour !")
