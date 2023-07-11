import logging

from celery import subtask
from app import celeryapp, db
from app.models.refs.siret import Siret

from app.services.siret import update_siret_from_api_entreprise
from app.clients.entreprise import  LimitHitError

from app.utilities.bucketting import which_bucket

__all__= ('update_one_fifth_of_sirets','update_all_siret_task',)

logger = logging.getLogger()
celery = celeryapp.celery

@celery.task(name='update_one_fifth_of_sirets', bind=True)
def update_one_fifth_of_sirets(self, which_fifth: int):

    buckets_size = 5
    if which_fifth < 0 or which_fifth > buckets_size:
        raise ValueError(f"which_fifth is {which_fifth}. It should be [0, {buckets_size}]")

    stmt = db.select(Siret.code).order_by(Siret.id)
    codes = db.session.execute(stmt).scalars()

    total = 0
    for i,code in enumerate(codes):

        code = int(code)
        bucket_number = which_bucket(code, buckets_size)
        if bucket_number != which_fifth:
            continue

        total += 1
        subtask("update_siret_task").delay(i, code)
    
    return f"Commande d'update envoyée pour {total} sirets"

@celery.task(name="update_all_siret_task", bind=True)
def update_all_siret_task(self):
    stmt = db.select(Siret.code).order_by(Siret.id)
    codes = db.session.execute(stmt).scalars()

    for i,code in enumerate(codes):
        subtask("update_siret_task").delay(i, code)

@celery.task(name="update_siret_task", bind=True)
def update_siret_task(self, index: int, code: str):
    try:
        siret = update_siret_from_api_entreprise(code)
    except LimitHitError as e:
        delay = (e.delay) + 5
        logger.info(
            f"[UPDATE][SIRET][{code}] Limite d'appel à l'API atteinte "
            f"Ré essai de la tâche dans {str(delay)} secondes")
        # XXX: max_retries=None ne désactive pas le mécanisme 
        # de retry max contrairement à ce que stipule la doc !
        # on met donc un grand nombre.
        self.retry(countdown=delay, max_retries=1000, retry_jitter=True)
        return

    try:
        db.session.add(siret)
        db.session.commit()
    except Exception as e:
        logger.error(f"[UPDATE][SIRET][{code}] Erreur lors de la mise à jour en base de données. Rollback.")
        db.session.rollback()
        raise