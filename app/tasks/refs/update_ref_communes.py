import os
import requests
import shutil
import tempfile
import logging
import json

import pandas as pd

from datetime import datetime
from flask import current_app
from celery import subtask

from app import celeryapp
from app.services.communes import select_communes_id, set_communes_non_pvd, set_communes_pvd
from app.tasks import limiter_queue
from app.tasks.financial import logger

_celery = celeryapp.celery
_logger = logging.getLogger(__name__)


@_celery.task(bind=True, name="import_file_pvd_from_website")
def import_file_pvd_from_website(self, url: str):
    response = requests.get(url, stream=True)
    response.raise_for_status()

    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                temp_file.write(chunk)

        _logger.info("Fichier téléchargé. Import...")
        _send_subtask_pvd_file(temp_file.name)


@limiter_queue(queue_name="file")
def _send_subtask_pvd_file(filepath: str):
    subtask("import_file_pvd").delay(filepath)


@_celery.task(bind=True, name="import_file_pvd")
def import_file_pvd(self, fichier: str):
    # get file
    _logger.info(f"[IMPORT][PVD] Start for file {fichier}")
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    move_folder = current_app.config["UPLOAD_FOLDER"] + "/save/"

    try:
        print(fichier)
        data_pvd_chunk = pd.read_csv(
            fichier,
            sep=",",
            header=0,
            dtype={"insee_com": str, "lib_com": str, "date_signature": str},
            chunksize=1000,
        )

        set_communes_non_pvd()

        for chunk in data_pvd_chunk:
            updates_to_commit = []

            # Récupération des dates de signature pour chaque commune
            dates_by_code = dict()
            for _, pvd_data in chunk.iterrows():
                commune_json = json.loads(pvd_data.to_json())
                code_commune = commune_json.get("insee_com", None)
                date_signature = commune_json.get("date_signature", None)
                dates_by_code[code_commune] = date_signature

            # Select communes => [(Commune.id, Commune.code), .. ]
            communes = select_communes_id(dates_by_code.keys())
            for commune in communes:
                date_signature = dates_by_code[commune[1]]
                date_signature = datetime.strptime(date_signature, "%Y-%m-%d") if date_signature is not None else None
                updates_to_commit.append({"id": commune[0], "is_pvd": True, "date_pvd": date_signature})

            # Bulk update
            set_communes_pvd(updates_to_commit)

        move_folder = os.path.join(move_folder, timestamp)
        if not os.path.exists(move_folder):
            os.makedirs(move_folder)
        logger.info(f"[IMPORT][PVD] Save file {fichier} in {move_folder}")

        shutil.move(fichier, move_folder)
        logger.info("[IMPORT][PVD] End")

        return True
    except Exception as e:
        logger.exception(f"[IMPORT][PVD] Error lors de l'import du fichier PVD: {fichier}")
        raise e
