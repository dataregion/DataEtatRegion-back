import logging
import os
import tempfile
import zipfile

import pandas
from datetime import datetime
import numpy as np
import requests
from celery import subtask
from flask import current_app

from app import celeryapp, db
from models.entities.refs.Siret import Siret

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
            f"[UPDATE][SIRET][{code}] Limite d'appel à l'API atteinte Ré essai de la tâche dans {str(delay)} secondes"
        )
        # XXX: max_retries=None ne désactive pas le mécanisme
        # de retry max contrairement à ce que stipule la doc !
        # on met donc un grand nombre.
        self.retry(countdown=delay, max_retries=1000, retry_jitter=True)
        return

    try:
        db.session.add(siret)
        db.session.commit()
    except Exception as _:
        logger.error(f"[UPDATE][SIRET][{code}] Erreur lors de la mise à jour en base de données. Rollback.")
        db.session.rollback()
        raise


@celery.task(name="update_link_siret_qpv_from_website", bind=True)
def update_link_siret_qpv_from_website(self, url: str = "", day_of_week: int = 5, qpv_colname: str = "plg_qp15"):
    """
    Télécharge le fichier des liens QPV/Siret et lance la mise à jours des liens
    :param self:
    :param qpv_colname: la colonne des QPV a utiliser ex: plg_qp15 ou plg_qp24
    :return:
    """
    today = datetime.today()
    # Vérifie que c’est le deuxième day of week du mois
    if today.weekday() != day_of_week or not (8 <= today.day <= 15):
        logger.info(f"Tâche ignorée : aujourd'hui ({today.date()}) n'est pas le second {day_of_week} du mois.")
        return

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
                        usecols=["siret", qpv_colname],
                        chunksize=100000,
                        sep=";",
                        dtype={"siret": str, qpv_colname: str},
                    )
                    resultats = []

                    # Parcourir les chunks et filtrer les lignes
                    for chunk in chunks:
                        filtre = ~chunk[qpv_colname].isin(["CSZ", "HZ", " ", ""])
                        morceau_filtre = chunk[filtre]
                        resultats.append(morceau_filtre)

                    # Concaténer les morceaux filtrés en un seul DataFrame
                    df_final = pandas.concat(resultats, ignore_index=True)
                    save_path = os.path.join(current_app.config["UPLOAD_FOLDER"], "qpv.csv")
                    # with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as temp_file:
                    # Écrivez le DataFrame dans le fichier CSV temporaire
                    df_final.to_csv(save_path, index=False)
                    subtask("update_link_siret_qpv").delay(save_path, qpv_colname=qpv_colname)
            break
        # # Initialiser une liste pour stocker les morceaux filtrés


@celery.task(name="update_link_siret_qpv", bind=True)
def update_link_siret_qpv(self, file: str, qpv_colname: str = "plg_qp15", page_number: int = 1):
    """
    Mise à jours de liens Siret QPV
    Tache récursive, qui tant qu'il y a une page suivante, lance une nouvelle tache update_link_siret_qpv
    :param self:
    :param file: Le fichier contenant les siret et QPV
    :param page: le numéro de page des siret à mettre à jours.
    :param qpv_colname: la colonne des QPV a utiliser ex: plg_qp15 ou plg_qp24
    :return:
    """
    logger.info(f"[TASK][SIRET]Update lien QPV siret de la page {page_number}")
    all_siret_qpv = pandas.read_csv(file, header=0, usecols=["siret", qpv_colname], sep=",", dtype={"siret": str})

    all_siret_qpv = all_siret_qpv.replace({np.nan: None})

    stmt = db.select(Siret).order_by(Siret.id)
    page_result = db.paginate(stmt, per_page=1000, error_out=False, page=page_number)
    total_page = page_result.pages  # on récupère le nombre de pages
    logger.info("[TASK][SIRET] Parcours des 1000 Siret")

    siret_qpv_colname = "code_qpv15"
    if qpv_colname == "plg_qp24":
        siret_qpv_colname = "code_qpv24"

    for siret in page_result.items:
        search_qpv = all_siret_qpv[all_siret_qpv["siret"] == siret.code]
        # Vérifiez si des lignes correspondent
        if len(search_qpv) == 0:
            if getattr(siret, siret_qpv_colname) is not None:
                db.session.execute(db.update(Siret).where(Siret.code == siret.code).values({siret_qpv_colname: None}))
                logger.info(f"[TASK][SIRET] Le siret {getattr(siret, siret_qpv_colname)} n'est plus dans un QPV")
            logger.debug(f"[TASK][SIRET] Pas de Qpv pour le siret {getattr(siret, siret_qpv_colname)}")
        else:
            code_qpv = search_qpv[qpv_colname].values[0]
            logger.info(f"[TASK][SIRET] Qpv {code_qpv} trouvé pour le siret {getattr(siret, siret_qpv_colname)}")
            db.session.execute(db.update(Siret).where(Siret.code == siret.code).values({siret_qpv_colname: code_qpv}))
    db.session.commit()

    if page_number <= total_page:
        logger.info(f"[TASK][SIRET] Il reste {total_page - page_number}  pages. Lancement de la tâche suivante")
        subtask("update_link_siret_qpv").delay(file, qpv_colname=qpv_colname, page_number=(page_number + 1))
    else:
        logger.info("[TASK][SIRET] Fin de la mise à jours des liens Siret Qpv.")
