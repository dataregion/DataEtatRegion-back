import logging
import os
import json
import shutil
import datetime

import pandas
from celery import subtask, current_task
from flask import current_app

from sqlalchemy import delete, select, asc

from app import celeryapp, db
from app.models.audit.AuditUpdateData import AuditUpdateData
from app.models.audit.AuditInsertFinancialTasks import AuditInsertFinancialTasks
from app.models.enums.DataType import DataType
from app.services.financial_data import delete_ae_no_cp_annee_region, delete_cp_annee_region
from app.tasks.financial import LineImportTechInfo

from app.tasks.financial.import_financial import _send_subtask_financial_ae, _send_subtask_financial_cp
from app.models.financial.FinancialAe import FinancialAe
from app.models.financial.FinancialCp import FinancialCp

celery = celeryapp.celery


DEFAULT_MAX_ROW = 10000  # 10K


@celery.task(bind=True, name="delayed_inserts")
def delayed_inserts(self):
    # Si on trouve des tâches dans la table, on les récupère pour les éxécuter
    # On dépile en fifo pour chaque region
    result = db.session.execute(select(AuditInsertFinancialTasks.source_region).distinct())
    regions = [row[0] for row in result.fetchall()]

    for region in regions:
        stmt = (
            select(AuditInsertFinancialTasks)
            .where(AuditInsertFinancialTasks.source_region == region)
            .order_by(asc(AuditInsertFinancialTasks.id))
            .limit(1)
        )
        task = db.session.execute(stmt).scalar()

        # Nettoyage de la BDD
        delete_cp_annee_region(task.annee, task.source_region)
        delete_ae_no_cp_annee_region(task.annee, task.source_region)
        # Tâche d'import des AE et des CP
        split_csv_and_import_ae_and_cp.delay(
            task.fichier_ae,
            task.fichier_cp,
            json.dumps({"sep": ",", "skiprows": 8}),
            source_region=task.source_region,
            annee=task.annee,
        )
        # Historique de chargement des données
        db.session.add(
            AuditUpdateData(
                username=task.username,
                filename=os.path.basename(task.fichier_ae),
                data_type=DataType.FINANCIAL_DATA_AE,
            )
        )
        db.session.add(
            AuditUpdateData(
                username=task.username,
                filename=os.path.basename(task.fichier_cp),
                data_type=DataType.FINANCIAL_DATA_CP,
            )
        )

        # Suppression de la tâche dans la table
        db.session.execute(delete(AuditInsertFinancialTasks).where(AuditInsertFinancialTasks.id == task.id))
    db.session.commit()


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
    move_folder = os.path.join(current_app.config["UPLOAD_FOLDER"], "save", datetime.datetime.now().strftime("%Y%m%d"))
    if not os.path.exists(move_folder):
        os.makedirs(move_folder)

    # Parsing des fichiers
    ae_list, cp_list = _parse_file(
        DataType.FINANCIAL_DATA_AE, fichierAe, source_region, annee, csv_options, move_folder, {}, {}
    )
    ae_list, cp_list = _parse_file(
        DataType.FINANCIAL_DATA_CP, fichierCp, source_region, annee, csv_options, move_folder, ae_list, cp_list
    )

    # Sauvegarde des fichiers complets
    _move_file(fichierAe, current_app.config["UPLOAD_FOLDER"] + "/save/")
    _move_file(fichierCp, current_app.config["UPLOAD_FOLDER"] + "/save/")

    # Import de toutes les AE ainsi que leur CP associés
    index = 0
    for key in ae_list:
        for ae in ae_list[key]["ae"]:
            _send_subtask_financial_ae(ae, source_region, annee, index, ae_list[key]["cp"])
            index += 1

    # Import de tous les CP ans AE
    index = 0
    for key in cp_list:
        _send_subtask_financial_cp(cp_list[key]["data"], key, source_region, annee, cp_list[key]["task"])
        index += 1


def _parse_file(
    data_type: DataType,
    fichier: str,
    source_region: str,
    annee: int,
    csv_options: str,
    move_folder: str,
    ae_list: dict,
    cp_list: dict,
):
    """
    Split un fichier en plusieurs fichiers et autant de tâches qu'il y a de fichier
    :param data_type: Type de donnée à parser dans le fichier
    :param fichier: Le fichier à parser
    :param source_region: Région de l'exercice comptable
    :param annee: Année de l'exercice comptable
    :param csv_options: Options pour la lecture du fichier par pandas.read_csv
    :param move_folder: Dossier de sauvegarde pour les fichiers chunk
    :param ae_list: Dictionnaire contenant les infos des AE à insérer
    :param cp_list: Dictionnaire contenant les infos des CP à insérer
    :return:
    """
    filename = os.path.splitext(os.path.basename(fichier))[0]
    max_lines = (
        DEFAULT_MAX_ROW if "SPLIT_FILE_LINE" not in current_app.config else current_app.config["SPLIT_FILE_LINE"]
    )
    logging.info(f"[IMPORT][SPLIT][{data_type}] Split du fichier en chunk de {max_lines} lignes")

    try:
        chunk_index = 1
        chunks = pandas.read_csv(fichier, chunksize=max_lines, **json.loads(csv_options))
        for df in chunks:
            # Construire le nom de fichier de sortie
            output_file = os.path.join(current_app.config["UPLOAD_FOLDER"], f"{filename}_{chunk_index}.csv")
            df.to_csv(output_file, index=False)
            logging.info(f"[IMPORT][SPLIT] Création du fichier {output_file} de {min(max_lines, len(df.index))} lignes")
            try:
                if data_type is DataType.FINANCIAL_DATA_AE:
                    ae_list = _parse_file_ae(output_file, source_region, annee, ae_list)
                elif data_type is DataType.FINANCIAL_DATA_CP:
                    ae_list, cp_list = _parse_file_cp(
                        output_file, source_region, annee, chunk_index, max_lines, ae_list, cp_list
                    )
                shutil.copy(output_file, move_folder)
                logging.info(
                    f"[IMPORT][FINANCIAL][{data_type}] Sauvegarde du chunk {output_file} dans le dossier {move_folder}"
                )
            except Exception as e:
                logging.exception(f"[IMPORT][FINANCIAL][{data_type}] Error lors de l'import du fichier {output_file}")
                raise e
            chunk_index += 1
    except Exception as e:
        logging.exception(f"[IMPORT][FINANCIAL][{data_type}] Error lors de l'import du fichier {fichier}")
        raise e
    logging.info(f"[IMPORT][SPLIT][{data_type}] Fichier traité : {chunk_index - 1} fichier(s) créé(s)")
    return ae_list, cp_list


def _parse_file_ae(output_file: str, source_region: str, annee: int, ae_list: dict):
    """
    Parsing du fichier des AE
    :param output_file: Le fichier chunk à parser
    :param source_region: Région de l'exercice comptable
    :param annee: Année de l'exercice comptable
    :param ae_list: Dictionnaire contenant les infos des AE à insérer
    :return:
    """
    series = pandas.Series({f"{FinancialAe.annee.key}": annee, f"{FinancialAe.source_region.key}": source_region})
    data_chunk = pandas.read_csv(
        output_file,
        sep=",",
        header=0,
        names=FinancialAe.get_columns_files_ae(),
        dtype={
            "programme": str,
            "n_ej": str,
            "n_poste_ej": int,
            "fournisseur_titulaire": str,
            "siret": str,
        },
        chunksize=1000,
    )
    for chunk in data_chunk:
        for i, line in chunk.iterrows():
            key = f"{source_region}_{annee}_{line[FinancialAe.n_ej.key]}_{line[FinancialAe.n_poste_ej.key]}"
            ae = pandas.concat([line, series]).to_json()
            if key not in ae_list:
                ae_list[key] = {"ae": [], "cp": []}
            ae_list[key]["ae"].append(ae)
    return ae_list


def _parse_file_cp(
    output_file: str, source_region: str, annee: int, chunk_index: int, max_lines: int, ae_list: dict, cp_list: dict
):
    """
    Parsing du fichier des CP
    :param output_file: Le fichier chunk à parser
    :param source_region: Région de l'exercice comptable
    :param annee: Année de l'exercice comptable
    :param chunk_index: N° du chunk en train d'être parsé
    :param max_lines: Nombre maximum de lignes dans un chunk
    :param ae_list: Dictionnaire contenant les infos des AE et leurs CP à insérer
    :param cp_list: Dictionnaire contenant les infos des CP sans AE à insérer
    :return:
    """
    data_chunk = pandas.read_csv(
        output_file,
        sep=",",
        header=0,
        names=FinancialCp.get_columns_files_cp(),
        dtype=str,
        chunksize=1000,
    )
    for chunk in data_chunk:
        for i, line in chunk.iterrows():
            key = f"{source_region}_{annee}_{line[FinancialAe.n_ej.key]}_{line[FinancialAe.n_poste_ej.key]}"
            if key in ae_list.keys():
                ae_list[key]["cp"] += [
                    {
                        "data": line.to_json(),
                        "task": LineImportTechInfo(current_task.request.id, (chunk_index - 1) * max_lines + i),
                    }
                ]
            else:
                cp_list[f"{(chunk_index - 1) * max_lines + i}"] = {
                    "data": line.to_json(),
                    "task": LineImportTechInfo(current_task.request.id, (chunk_index - 1) * max_lines + i),
                }
    return ae_list, cp_list


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
