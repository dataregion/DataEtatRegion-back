import os
import requests
import shutil
import tempfile
import logging

import pandas as pd

from datetime import datetime
from flask import current_app
from celery import current_task, subtask

from app import celeryapp
from app.services.communes import select_commune, set_pvd, set_communes_non_pvd
from app.tasks import limiter_queue
from app.tasks.financial.errors import _handle_exception_import
from app.tasks.financial import logger, LineImportTechInfo

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


@limiter_queue(queue_name="line")
def _send_subtask_pvd(data_pvd: str, tech_info: LineImportTechInfo):
    subtask("import_line_pvd").delay(data_pvd, tech_info)


@_celery.task(bind=True, name="import_file_pvd")
def import_file_pvd(self, fichier: str):
    # get file
    _logger.info(f"[IMPORT][PVD] Start for file {fichier}")
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    move_folder = current_app.config["UPLOAD_FOLDER"] + "/save/"

    try:
        current_taskid = current_task.request.id
        data_pvd_chunk = pd.read_csv(
            fichier,
            sep=",",
            header=0,
            dtype={"insee_com": str, "lib_com": str, "date_signature": str},
            chunksize=1000,
        )

        set_communes_non_pvd()

        i = 0
        for chunk in data_pvd_chunk:
            for _, pvd_data in chunk.iterrows():
                i += 1
                tech_info = LineImportTechInfo(current_taskid, i)
                _send_subtask_pvd(pvd_data.to_json(), tech_info)

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


@_celery.task(bind=True, name="import_line_pvd")
@_handle_exception_import("PVD")
def import_line_pvd(self, commune_json, tech_info_list: list):
    code_commune = commune_json.get("insee_com", None)
    label_commune = commune_json.get("lib_com", None)
    date_signature = commune_json.get("date_signature", None)

    _logger.debug(f"Commune PVD : {code_commune} - {label_commune}")
    commune = select_commune(code_commune, label_commune)
    set_pvd(commune, datetime.strptime(date_signature, "%Y-%m-%d") if date_signature is not None else None)
