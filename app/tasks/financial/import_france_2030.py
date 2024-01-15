import json
import os
import shutil
import datetime

import pandas
from celery import subtask, current_task
from flask import current_app

from app import celeryapp, db
from app.models.financial.France2030 import France2030
from app.services.siret import check_siret
from app.tasks import logger, limiter_queue, LineImportTechInfo
from app.tasks.financial.errors import _handle_exception_import

celery = celeryapp.celery


@celery.task(bind=True, name="import_file_france_2030")
def import_file_france_2030(self, fichier: str, annee: int):
    # get file
    logger.info(f"[IMPORT][FRANCE 2030]Start file {fichier}")
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

    move_folder = current_app.config["UPLOAD_FOLDER"] + "/save/"
    try:
        current_taskid = current_task.request.id
        _chunksize = 1000

        chunked = pandas.read_csv(
            fichier,
            header=0,
            chunksize=_chunksize,
            dtype={
                "montant_subvention": str,
                "montant_avance_remboursable": str,
                "montant_aide": str,
                "siret": str,
            },
        )
        additionnal_line_info = pandas.Series({f"{France2030.annee.key}": annee})
        for chunk in chunked:
            # Gestion des valeurs numériques
            for field in ["montant_subvention", "montant_avance_remboursable", "montant_aide"]:
                chunk[field] = pandas.to_numeric(chunk[field], errors="coerce").astype(float)

            for i, row in chunk.iterrows():
                tech_info = LineImportTechInfo(current_taskid, i)
                line = pandas.concat([row, additionnal_line_info])
                _send_subtask_france_2030(line.to_json(), tech_info)

        move_folder = os.path.join(move_folder, timestamp)
        if not os.path.exists(move_folder):
            os.makedirs(move_folder)
        logger.info(f"[IMPORT][FRANCE 2030] Save file {fichier} in {move_folder}")
        shutil.move(fichier, move_folder)
        logger.info("[IMPORT][FRANCE 2030] End")

        return True
    except Exception as e:
        logger.exception(f"[IMPORT][FRANCE 2030] Error lors de l'import du fichier {fichier}")
        raise e


@limiter_queue(queue_name="line")
def _send_subtask_france_2030(line, tech_info: LineImportTechInfo):
    subtask("import_line_france_2030").delay(line, tech_info)


@celery.task(bind=True, name="import_line_france_2030")
@_handle_exception_import("FRANCE_2030")
def import_line_france_2030(self, line: str, tech_info_list: list):
    logger.debug(f"[IMPORT][FRANCE 2030][LINE] Traitement de la ligne ademe: {tech_info_list}")
    logger.debug(f"[IMPORT][FRANCE 2030][LINE] Contenu de la ligne FRANCE_2030 : {line}")
    logger.debug(f"[IMPORT][FRANCE 2030][LINE] Contenu du tech info      : {tech_info_list}")

    tech_info = LineImportTechInfo(*tech_info_list)

    line = json.loads(line)
    france_2030 = France2030(**line)
    france_2030.file_import_taskid = tech_info.file_import_taskid
    france_2030.file_import_lineno = tech_info.lineno

    logger.info(f"[IMPORT][FRANCE 2030][LINE] Tentative ligne France 2030 beneficiaire {france_2030.siret}")
    # SIRET beneficiaire
    check_siret(france_2030.siret)

    db.session.add(france_2030)
    logger.info("[IMPORT][FRANCE 2030][LINE] Ajout ligne france 2030")
    db.session.commit()

    logger.debug(f"[IMPORT][FRANCE 2030][LINE] Traitement de la ligne france 2030: {tech_info_list}")
