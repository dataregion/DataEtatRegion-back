import logging
import os
import json
import shutil
import datetime

import pandas
from celery import subtask, current_task
from flask import current_app
from app import celeryapp
from app.tasks.financial import LineImportTechInfo

from app.tasks.financial.import_financial import _send_subtask_financial_ae, _send_subtask_financial_cp
from app.models.financial.FinancialAe import FinancialAe
from app.models.financial.FinancialCp import FinancialCp

celery = celeryapp.celery


DEFAULT_MAX_ROW = 10000  # 10K


@celery.task(bind=True, name="split_csv_and_import_ae_and_cp")
def split_csv_and_import_ae_and_cp(
    self, fichierAe: str, fichierCp: str, csv_options: str, source_region: str, annee: int
):
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
    filename_ae = os.path.splitext(os.path.basename(fichierAe))[0]
    filename_cp = os.path.splitext(os.path.basename(fichierCp))[0]
    move_folder = os.path.join(current_app.config["UPLOAD_FOLDER"], "save", datetime.datetime.now().strftime("%Y%m%d"))
    series = pandas.Series({f"{FinancialAe.annee.key}": annee, f"{FinancialAe.source_region.key}": source_region})
    if not os.path.exists(move_folder):
        os.makedirs(move_folder)
    logging.info(f"[IMPORT][SPLIT] Split du fichier des AE en chunk de {max_lines} lignes")

    ae_list = {}
    cp_list = {}
    try:
        chunk_index = 1
        chunks = pandas.read_csv(fichierAe, chunksize=max_lines, **json.loads(csv_options))
        for df in chunks:
            # Construire le nom de fichier de sortie
            output_file = os.path.join(current_app.config["UPLOAD_FOLDER"], f"{filename_ae}_{chunk_index}.csv")
            df.to_csv(output_file, index=False)
            logging.info(f"[IMPORT][SPLIT] Création du fichier {output_file} de {min(max_lines, len(df.index))} lignes")
            try:
                data_chunk = pandas.read_csv(
                    output_file, sep=",", header=0, names=FinancialAe.get_columns_files_ae(), dtype=str, chunksize=1000
                )
                for chunk in data_chunk:
                    for i, line in chunk.iterrows():
                        key = f"{source_region}_{annee}_{line[FinancialAe.n_ej.key]}_{line[FinancialAe.n_poste_ej.key]}"
                        ae = pandas.concat([line, series]).to_json()
                        if key not in ae_list:
                            ae_list[key] = {"ae": [], "cp": []}
                        ae_list[key]["ae"].append(ae)
                shutil.copy(output_file, move_folder)
                logging.info(f"[IMPORT][FINANCIAL][AE] Sauvegarde du chunk {output_file} dans le dossier {move_folder}")
            except Exception as e:
                logging.exception(f"[IMPORT][FINANCIAL][AE] Error lors de l'import du fichier {output_file}")
                raise e
            chunk_index += 1
    except Exception as e:
        logging.exception(f"[IMPORT][FINANCIAL][AE] Error lors de l'import du fichier {fichierAe}")
        raise e
    logging.info(f"[SPLIT] Fichiers des AE traité : {chunk_index - 1} fichier(s) créé(s)")

    try:
        chunk_index = 1
        chunks = pandas.read_csv(fichierCp, chunksize=max_lines, **json.loads(csv_options))
        for df in chunks:
            # Construire le nom de fichier de sortie
            output_file = os.path.join(current_app.config["UPLOAD_FOLDER"], f"{filename_cp}_{chunk_index}.csv")
            df.to_csv(output_file, index=False)
            logging.info(f"[IMPORT][SPLIT] Création du fichier {output_file} de {min(max_lines, len(df.index))} lignes")
            try:
                data_chunk = pandas.read_csv(
                    output_file, sep=",", header=0, names=FinancialCp.get_columns_files_cp(), dtype=str, chunksize=1000
                )
                for chunk in data_chunk:
                    for i, line in chunk.iterrows():
                        key = f"{source_region}_{annee}_{line[FinancialAe.n_ej.key]}_{line[FinancialAe.n_poste_ej.key]}"
                        if key in ae_list.keys():
                            ae_list[key]["cp"] += [
                                {
                                    "data": line.to_json(),
                                    "task": LineImportTechInfo(
                                        current_task.request.id, (chunk_index - 1) * max_lines + i
                                    ),
                                }
                            ]
                        else:
                            cp_list[f"{(chunk_index - 1) * max_lines + i}"] = {
                                "data": line.to_json(),
                                "task": LineImportTechInfo(current_task.request.id, (chunk_index - 1) * max_lines + i),
                            }
                shutil.copy(output_file, move_folder)
                logging.info(f"[IMPORT][FINANCIAL][CP] Sauvegarde du chunk {output_file} dans le dossier {move_folder}")
            except Exception as e:
                logging.exception(f"[IMPORT][FINANCIAL][CP] Error lors de l'import du fichier {output_file}")
                raise e
            chunk_index += 1
    except FileNotFoundError as dnf:
        logging.exception(f"[IMPORT][FINANCIAL][AE] Fichier {fichierCp} non trouvé")
        raise dnf
    logging.info(f"[SPLIT] Fichiers des CP traité : {chunk_index - 1} fichier(s) créé(s)")

    _move_file(fichierAe, current_app.config["UPLOAD_FOLDER"] + "/save/")
    _move_file(fichierCp, current_app.config["UPLOAD_FOLDER"] + "/save/")

    index = 0
    for key in ae_list:
        for ae in ae_list[key]["ae"]:
            _send_subtask_financial_ae(ae, source_region, annee, index, ae_list[key]["cp"])
            index += 1

    index = 0
    for key in cp_list:
        _send_subtask_financial_cp(cp_list[key]["data"], key, source_region, annee, cp_list[key]["task"])
        index += 1


# TODO : deprecated
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

    logging.info(f"[FILE] Sauvegarde du fichier {fichier} dans le dossier {move_folder}")
    shutil.move(fichier, move_folder)
