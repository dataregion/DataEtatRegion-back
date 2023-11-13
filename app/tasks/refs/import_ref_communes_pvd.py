import re
import traceback
from collections import namedtuple
import pandas as pd

import logging
from app import celeryapp
from app.services.communes import select_commune, set_pvd, set_communes_non_pvd


_celery = celeryapp.celery
_logger = logging.getLogger(__name__)

# __all__ = ("put_pvd_to_communes",)

# _headers_type = namedtuple("_headers_type", ["insee_com", "lib_com", "date_signature"])
# PUT_PVD_CSV_HEADERS = _headers_type(
#     insee_com = ["code", "insee_com"],
#     lib_com = ["label_commune", "lib_com"],
#     date_signature = ["date_signature_pvd", "date_signature"],
# )
# """Headers CSV nécessaires pour la commande de put des tags"""
# PUT_PVD_CSV_CHUNKSIZE = 1_000
# """Taille du chunk pour la lecture du fichier de commande de maj de tags"""


import json
import os
import requests
import shutil
import tempfile

from datetime import datetime
from flask import current_app

from app.tasks import limiter_queue
from celery import current_task, subtask
from app.tasks.financial.errors import _handle_exception_import
from app.tasks.financial import logger, LineImportTechInfo


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
def _send_subtask_pvd(data_ademe: str, tech_info: LineImportTechInfo):
    subtask("import_line_pvd").delay(data_ademe, tech_info)





@_celery.task(bind=True, name="import_file_pvd")
def import_file_pvd(self, fichier: str):
    # get file
    _logger.info(f"[IMPORT][PVD] Start for file {fichier}")
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

    move_folder = current_app.config["UPLOAD_FOLDER"] + "/save/"

    try:
        current_taskid = current_task.request.id
        data_pvd_chunk = pd.read_csv(
            fichier,
            sep=",",
            header=0,
            dtype={"pourcentageSubvention": float, "idBeneficiaire": str, "idAttribuant": str, "notificationUE": str},
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
        logger.exception(f"[IMPORT][PVD] Error lors de l'import du fichier ademe: {fichier}")
        raise e


@_celery.task(bind=True, name="import_line_pvd")
@_handle_exception_import("PVD")
def import_line_pvd(self, line_commune: str, tech_info_list: list):
    code_commune = line_commune.get("insee_com", None)
    label_commune = line_commune.get("lib_com", None)

    _logger.debug(f"Commune PVD : {code_commune} - {label_commune}")
    commune = select_commune(code_commune, label_commune)
    return set_pvd(commune)














# @_celery.task(bind=True, name="put_pvd_to_communes")
# def put_pvd_to_communes(self):
#     """
#     Applique les tags aux AE depuis un export csv utilisateur.
#     Cette tâche n'est pas idempotente et doit être rejouée par l'utilisateur si besoin.
#     """

#     report = {
#         "sent": 0,
#         "in-error-before-sending": 0,
#         "total": 0,
#         "last-traceback": [],
#     }

#     def process_line(line_dict):
#         try:
#             code_commune = _get_cell(line_dict, PUT_PVD_CSV_HEADERS.insee_com)
#             label_commune = _get_cell(line_dict, PUT_PVD_CSV_HEADERS.lib_com)
#             date_signature_pvd = _get_cell(line_dict, PUT_PVD_CSV_HEADERS.date_signature)

#             put_pvd_to_commune.delay(code_commune, label_commune, date_signature_pvd)

#             _logger.debug(f"Ligne: {code_commune}, {label_commune} et {date_signature_pvd}")
#             report["sent"] += 1
#         except Exception as e:
#             _logger.warning("Echec lors du traitement de la ligne pour mise à jour de tag", exc_info=e)
#             _tb = traceback.format_exception(type(e), e, e.__traceback__)
#             report["in-error-before-sending"] += 1
#             report["last-traceback"] = _tb

#     chunked = pd.read_csv(file, chunksize=PUT_PVD_CSV_CHUNKSIZE)
#     for chunk in chunked:
#         df = chunk
#         df = df.replace({pd.NA: None})  # XXX: important pour la gestion de valeur vides
#         dict_form = df.to_dict(orient="records")

#         for line_dict in dict_form:
#             print(line_dict)
#             process_line(line_dict)
#             report["total"] += 1

#     return report


# @_celery.task(bind=True, name="put_tags_to_ae")
# def put_pvd_to_commune(self, code_commune: str, label_commune: str):
#     _logger.debug(f"Application du tag PVD à la commune ({code_commune, {label_commune}})")
#     commune = select_commune(code_commune, label_commune)
#     return set_pvd(commune)


# def _get_cell(line_dict: dict, keys: list[str]):
#     """Retrieve a cell of the dict from a list of key synonyms"""
#     cell = None
#     for key in keys:
#         cell = line_dict.get(key, None)
#         if cell is not None:
#             break
#     return cell
