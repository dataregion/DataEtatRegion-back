import os
import shutil
import datetime

import pandas
from flask import current_app

from app import celeryapp
from app.models.financial.France2030 import France2030
from app.tasks import logger

celery = celeryapp.celery


@celery.task(bind=True, name='import_file_france_2030')
def import_file_france_2030(self, fichier: str, sheet_name: str = "Liste des projets et bénef", region : str | None= None):
    # get file
    logger.info(f'[IMPORT][FRANCE 2030]Start file {fichier}')
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

    move_folder = current_app.config['UPLOAD_FOLDER'] + "/save/"
    try:
        # noinspection PyTypeChecker
        df = pandas.read_excel(fichier, skiprows=3, sheet_name=sheet_name, usecols="B:Q", names=France2030.get_columns_files(),
                               dtype={'montant_subvention': float, 'montant_avance_remboursable': float,
                                      'montant_aide': float, 'siret': str})

        if region is not None :
            df = df[df['regions'] == region]

        for index, row in df.iterrows():
            print(row)
            # _send_subtask_financial_ae(line.append(series).to_json(), index, force_update)

        move_folder = os.path.join(move_folder, timestamp)
        if not os.path.exists(move_folder):
            os.makedirs(move_folder)
        logger.info(f'[IMPORT][FRANCE 2030] Save file {fichier} in {move_folder}')
        shutil.move(fichier, move_folder)
        logger.info('[IMPORT][FRANCE 2030] End')

        return True
    except Exception as e:
        logger.exception(f"[IMPORT][FRANCE 2030] Error lors de l'import du fichier {fichier}")
        raise e
