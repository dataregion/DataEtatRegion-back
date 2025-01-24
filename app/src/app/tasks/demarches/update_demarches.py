import json
import logging
from app.services.demarches.demarches import DemarcheService, get_reconciliation_form_data, get_affichage_form_data

from app.services.demarches.reconciliations import ReconciliationService
from celery import subtask
from app import celeryapp
from app.tasks import limiter_queue
from models.entities.demarches.Demarche import Demarche


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
    demarche: Demarche = DemarcheService.find(demarche_number)
    rec: dict | None = demarche.reconciliation if demarche.reconciliation else None
    aff: dict | None = demarche.affichage if demarche.affichage else None
    demarche = DemarcheService.integrer_demarche(uuid_user, token_id, demarche_number)

    if rec is not None:
        champs_reconciliation, cadre = get_reconciliation_form_data(rec)
        LOGGER.info(f"[UPDATE][DEMARCHE] Champs reconciliation : {json.dumps(champs_reconciliation)}")
        LOGGER.info(f"[UPDATE][DEMARCHE] Champs cadre : {json.dumps(cadre)}")
        ReconciliationService.do_reconciliation(demarche.number, champs_reconciliation, cadre)

    if aff is not None:
        affichage = get_affichage_form_data(aff)
        LOGGER.info(f"[UPDATE][DEMARCHE] Champs affichage : {json.dumps(affichage)}")
        DemarcheService.update_affichage(demarche_number, affichage)

    LOGGER.info(f"[UPDATE][DEMARCHE] Démarche {demarche.number} mise à jour !")
