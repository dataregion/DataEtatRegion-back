import logging
import os
import json
import shutil
import datetime

import pandas
from celery import subtask
from flask import current_app
from app import celeryapp

celery = celeryapp.celery


DEFAULT_MAX_ROW = 10000  # 10K


@celery.task(bind=True, name="split_csv_files_and_run_task")
def split_csv_files_and_run_task(self, fichier: str, task_name: str, csv_options: str, **kwargs):
    """
    Split un fichier en plusieurs fichiers et autant de tâches qu'il y a de fichier
    :param self:
    :param fichier: le fichier à splitter
    :param tastk_name:  le nom de la task à lancer pour chaque fichier
    :param kwargs:    la liste des args pour la sous tâche
    :return:
    """
    max_lines = (
        DEFAULT_MAX_ROW if "SPLIT_FILE_LINE" not in current_app.config else current_app.config["SPLIT_FILE_LINE"]
    )
    file_name = os.path.splitext(os.path.basename(fichier))[0]

    logging.info(f"[SPLIT] Start split file for task {task_name} in {max_lines} lines")

    chunks = pandas.read_csv(fichier, chunksize=max_lines, **json.loads(csv_options))
    index = 1
    for df in chunks:
        # Construire le nom de fichier de sortie
        output_file = os.path.join(current_app.config["UPLOAD_FOLDER"], f"{file_name}_{index}.csv")
        df.to_csv(output_file, index=False)
        logging.info(f"[SPLIT] Send task {task_name} with file {output_file} with param {kwargs}")

        subtask(task_name).delay(output_file, **kwargs)
        index += 1

    _move_file(fichier, current_app.config["UPLOAD_FOLDER"] + "/save/")
    logging.info(f"[SPLIT] End split file for task {task_name}")


def _move_file(fichier: str, move_folder: str):
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    move_folder = os.path.join(move_folder, timestamp)
    if not os.path.exists(move_folder):
        os.makedirs(move_folder)

    logging.info(f"[FILE] Save file {fichier} in {move_folder}")
    shutil.move(fichier, move_folder)
