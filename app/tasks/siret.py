import logging
import tempfile
import zipfile

import pandas
import requests
from celery import subtask
from flask import current_app

from app import celeryapp, db
from app.exceptions.exceptions import ConfigurationException
from app.models.refs.siret import Siret

from app.services.siret import update_siret_from_api_entreprise
from app.clients.entreprise import LimitHitError

from app.utilities.bucketting import which_bucket

__all__ = (
    "update_one_fifth_of_sirets",
    "update_all_siret_task",
)

logger = logging.getLogger()
celery = celeryapp.celery


@celery.task(name="update_one_fifth_of_sirets", bind=True)
def update_one_fifth_of_sirets(self, which_fifth: int):
    buckets_size = 5
    if which_fifth < 0 or which_fifth > buckets_size:
        raise ValueError(f"which_fifth is {which_fifth}. It should be [0, {buckets_size}]")

    stmt = db.select(Siret.code).order_by(Siret.id)
    codes = db.session.execute(stmt).scalars()

    total = 0
    for i, code in enumerate(codes):
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

    for i, code in enumerate(codes):
        subtask("update_siret_task").delay(i, code)


@celery.task(name="update_siret_task", bind=True)
def update_siret_task(self, index: int, code: str):
    try:
        siret = update_siret_from_api_entreprise(code)
    except LimitHitError as e:
        delay = (e.delay) + 5
        logger.info(
            f"[UPDATE][SIRET][{code}] Limite d'appel à l'API atteinte "
            f"Ré essai de la tâche dans {str(delay)} secondes"
        )
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


@celery.task(name="update_link_siret_qpv_from_website", bind=True)
def update_link_siret_qpv_from_website(self, url: str):
    """
    Télécharge le fichier des liens QPV/Siret et lance la mise à jours des liens
    :param self:
    :return:
    """
    logger.info("Récupération du fichier des QPV/Siret")
    response = requests.get(url, stream=True)
    response.raise_for_status()

    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                temp_file.write(chunk)

        logger.info("Fichier téléchargé. Extraction zip...")

    with zipfile.ZipFile(temp_file.name, "r") as zip_file:
        for nom_fichier in zip_file.namelist():
            # Vérifier si le fichier a l'extension .csv
            if nom_fichier.lower().endswith(".csv"):
                # Extraire le fichier CSV
                with zip_file.open(nom_fichier) as csv_file:
                    logger.info("Extraction des infos du CSV ....")
                    chunks = pandas.read_csv(
                        csv_file,
                        header=0,
                        usecols=["siret", "plg_qp"],
                        chunksize=100000,
                        sep=";",
                        dtype={"siret": str, "plg_qp": str},
                    )
                    resultats = []

                    # Parcourir les chunks et filtrer les lignes
                    for chunk in chunks:
                        filtre = ~chunk["plg_qp"].isin(["CSZ", "HZ", " ", ""])
                        morceau_filtre = chunk[filtre]
                        resultats.append(morceau_filtre)

                    # Concaténer les morceaux filtrés en un seul DataFrame
                    df_final = pandas.concat(resultats, ignore_index=True)
                    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as temp_file:
                        # Écrivez le DataFrame dans le fichier CSV temporaire
                        df_final.to_csv(temp_file.name, index=False)
                        subtask("update_link_siret_qpv").delay(temp_file.name)
            break
        # # Initialiser une liste pour stocker les morceaux filtrés


@celery.task(name="update_link_siret_qpv", bind=True)
def update_link_siret_qpv(self, file: str):
    logger.info("[TASK][SIRET]Update lien QPV siret")
    all_siret_qpv = pandas.read_csv(file, header=0, usecols=["siret", "plg_qp"], sep=",", dtype={"siret": str})

    stmt = db.select(Siret).order_by(Siret.code)
    page = db.paginate(stmt, per_page=100, error_out=False)
    pagination = page.iter_pages()  # on récupère le nombre de pages
    logger.debug(f"[TASK][SIRET] Parcours de {page.pages} de 100 Siret")

    for page_number in pagination:
        logger.debug(f"[TASK][SIRET] Parcours de la page {page_number}")
        for siret in page.items:
            search_qpv = all_siret_qpv[all_siret_qpv["siret"] == siret.code]
            # Vérifiez si des lignes correspondent
            if len(search_qpv) == 0:
                if siret.code_qpv is not None:
                    db.session.execute(db.update(Siret).where(Siret.code == siret.code).values(code_qpv=None))
                    logger.info(f"[TASK][SIRET] Le siret {siret.code} n'est plus dans un QPV")
                logger.debug(f"[TASK][SIRET] Pas de Qpv pour le siret {siret.code}")
            else:
                code_qpv = search_qpv["plg_qp"].values[0]
                logger.info(f"[TASK][SIRET] Qpv {code_qpv} trouvé pour le siret {siret.code}")
                db.session.execute(db.update(Siret).where(Siret.code == siret.code).values(code_qpv=code_qpv))
        db.session.commit()
        page = page.next()

    logger.info("[TASK][SIRET] Fin de l'update des liens QPV siret")
