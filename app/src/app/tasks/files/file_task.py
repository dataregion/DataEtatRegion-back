import logging
import os
import json
import shutil
import datetime
from models.entities.refs.Region import get_code_region_by_code_comp
import pandas
from celery import subtask, current_task
from flask import current_app
from sqlalchemy import delete, select, asc
from app import celeryapp, db
from models.entities.audit.AuditUpdateData import AuditUpdateData
from models.entities.audit.AuditInsertFinancialTasks import AuditInsertFinancialTasks
from models.value_objects.common import DataType
from app.services.financial_data import (
    delete_ae_no_cp_annee_national,
    delete_ae_no_cp_annee_region,
    delete_cp_annee_national,
    delete_cp_annee_region,
)
from app.tasks.financial import LineImportTechInfo
from app.tasks.financial.import_financial import (
    _send_subtask_financial_ae,
    _send_subtask_financial_cp,
    get_batch_size,
)
from models.entities.financial.FinancialAe import FinancialAe
from models.entities.financial.FinancialCp import FinancialCp

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
        assert task is not None, "On doit avoir une tâche d'import obligatoirement."

        app_clientid = task.application_clientid

        if region != "NATIONAL":
            logging.info(f"[DELAYED] Delayed Insert sur region {region}")
            # Nettoyage de la BDD
            delete_cp_annee_region(task.annee, task.source_region)
            delete_ae_no_cp_annee_region(task.annee, task.source_region)
            # Tâche d'import des AE et des CP
            read_csv_and_import_ae_cp.delay(
                task.fichier_ae,
                task.fichier_cp,
                json.dumps({"sep": ",", "skiprows": 7}),
                source_region=task.source_region,
                annee=task.annee,
            )
        else:
            logging.info("[DELAYED] Delayed Insert sur NATIONAL")
            csv_options = json.dumps({"sep": '";"', "skiprows": 0, "dtype": "str"})
            # Nettoyage de la BDD
            delete_cp_annee_national(task.annee)
            delete_ae_no_cp_annee_national(task.annee)
            read_csv_and_import_fichier_nat_ae_cp.delay(task.fichier_ae, task.fichier_cp, csv_options, task.annee)

        # Historique de chargement des données
        db.session.add(
            AuditUpdateData(
                username=task.username,
                filename=os.path.basename(task.fichier_ae),
                data_type=DataType.FINANCIAL_DATA_AE,
                application_clientid=app_clientid,
                source_region=region,
            )
        )
        db.session.add(
            AuditUpdateData(
                username=task.username,
                filename=os.path.basename(task.fichier_cp),
                data_type=DataType.FINANCIAL_DATA_CP,
                application_clientid=app_clientid,
                source_region=region,
            )
        )

        # Suppression de la tâche dans la table
        db.session.execute(delete(AuditInsertFinancialTasks).where(AuditInsertFinancialTasks.id == task.id))
    db.session.commit()


@celery.task(bind=True, name="read_csv_and_import_fichier_nat_ae_cp")
def read_csv_and_import_fichier_nat_ae_cp(self, fichierAe: str, fichierCp: str, csv_options: str, annee: int):
    move_folder = os.path.join(current_app.config["UPLOAD_FOLDER"], "save", datetime.datetime.now().strftime("%Y%m%d"))
    if not os.path.exists(move_folder):
        os.makedirs(move_folder)

    # Parsing des fichiers
    ae_list, cp_list = _parse_generic(
        DataType.FINANCIAL_DATA_AE, fichierAe, None, annee, csv_options, move_folder, {}, {}, is_national=True
    )
    ae_list, cp_list = _parse_generic(
        DataType.FINANCIAL_DATA_CP, fichierCp, None, annee, csv_options, move_folder, ae_list, cp_list, is_national=True
    )

    # Sauvegarde des fichiers complets
    _move_file(fichierAe, current_app.config["UPLOAD_FOLDER"] + "/save/")
    _move_file(fichierCp, current_app.config["UPLOAD_FOLDER"] + "/save/")

    _process_batches(ae_list, cp_list, annee=annee)


@celery.task(bind=True, name="read_csv_and_import_ae_cp")
def read_csv_and_import_ae_cp(self, fichierAe: str, fichierCp: str, csv_options: str, source_region: str, annee: int):
    move_folder = os.path.join(current_app.config["UPLOAD_FOLDER"], "save", datetime.datetime.now().strftime("%Y%m%d"))
    if not os.path.exists(move_folder):
        os.makedirs(move_folder)

    # Parsing des fichiers
    ae_list, cp_list = _parse_generic(
        DataType.FINANCIAL_DATA_AE, fichierAe, source_region, annee, csv_options, move_folder, {}, {}, is_national=False
    )
    ae_list, cp_list = _parse_generic(
        DataType.FINANCIAL_DATA_CP,
        fichierCp,
        source_region,
        annee,
        csv_options,
        move_folder,
        ae_list,
        cp_list,
        is_national=False,
    )

    # Sauvegarde des fichiers complets
    _move_file(fichierAe, current_app.config["UPLOAD_FOLDER"] + "/save/")
    _move_file(fichierCp, current_app.config["UPLOAD_FOLDER"] + "/save/")

    _process_batches(ae_list, cp_list, source_region, annee)


def _process_batches(ae_list, cp_list, source_region=None, annee=None):
    index = 0
    ae_batch = []
    cp_lists = []
    while ae_list:
        _, struct = ae_list.popitem()
        lines = struct["ae"]
        for line in lines:
            ae_batch.append(line)
            cp_lists.extend(struct["cp"])
            if len(ae_batch) == get_batch_size():
                _send_subtask_financial_ae(ae_batch, source_region, annee, index, cp_lists)
                ae_batch, cp_lists = [], []
                index += get_batch_size()

    # Envoyer tout reste non envoyé
    if ae_batch:
        _send_subtask_financial_ae(ae_batch, source_region, annee, index, cp_lists)

    # Import de tous les CP sans AE
    index = 0
    cp_batch = []
    while cp_list:
        k, struct = cp_list.popitem()
        cp_batch.append(struct)
        if len(cp_batch) == get_batch_size():
            _send_subtask_financial_cp(cp_batch, source_region, annee, index)
            cp_batch = []
            index += get_batch_size()

    # Envoyer tout reste non envoyé
    if cp_batch:
        _send_subtask_financial_cp(cp_batch, source_region, annee, index)


def _parse_generic(
    data_type: DataType,
    fichier: str,
    source_region: str | None,
    annee: int | None,
    csv_options: str,
    move_folder: str,
    ae_list: dict,
    cp_list: dict,
    is_national: bool = False,
) -> list[dict]:
    """
    Split un fichier en plusieurs fichiers et autant de tâches qu'il y a de fichier.
    Gère à la fois les fichiers régionaux et nationaux.
    """
    filename = os.path.splitext(os.path.basename(fichier))[0]
    max_lines = current_app.config.get("SPLIT_FILE_LINE", DEFAULT_MAX_ROW)
    logging.info(f"[IMPORT][SPLIT][{data_type}] Split du fichier en chunk de {max_lines} lignes")

    try:
        chunk_index = 1
        chunks = pandas.read_csv(fichier, chunksize=max_lines, **json.loads(csv_options))
        for df in chunks:
            output_file = os.path.join(current_app.config["UPLOAD_FOLDER"], f"{filename}_{chunk_index}.csv")
            df.to_csv(output_file, index=False)
            logging.info(f"[IMPORT][SPLIT] Création du fichier {output_file} de {min(max_lines, len(df.index))} lignes")

            try:
                if data_type == DataType.FINANCIAL_DATA_AE:
                    ae_list = _parse_ae(output_file, ae_list, source_region, annee, is_national)
                elif data_type == DataType.FINANCIAL_DATA_CP:
                    ae_list, cp_list = _parse_cp(
                        output_file, chunk_index, max_lines, ae_list, cp_list, source_region, annee, is_national
                    )
                shutil.copy(output_file, move_folder)
            except Exception as e:
                logging.exception(
                    f"[IMPORT][FINANCIAL][{data_type}] Error lors de l'import du fichier {output_file}: {e}"
                )
                raise e

            chunk_index += 1
    except Exception as e:
        logging.exception(f"[IMPORT][FINANCIAL][{data_type}] Error lors de l'import du fichier {fichier}: {e}")
        raise e

    return ae_list, cp_list


def _parse_ae(output_file: str, ae_list: dict, source_region: str | None, annee: int | None, is_national: bool):
    if is_national:
        return _parse_fichier_nat_ae(output_file, annee, ae_list)
    else:
        return _parse_file_ae(output_file, source_region, annee, ae_list)


def _parse_cp(
    output_file: str,
    chunk_index: int,
    max_lines: int,
    ae_list: dict,
    cp_list: dict,
    source_region: str | None,
    annee: int | None,
    is_national: bool,
):
    if is_national:
        return _parse_fichier_nat_cp(output_file, annee, chunk_index, max_lines, ae_list, cp_list)
    else:
        return _parse_file_cp(output_file, source_region, annee, chunk_index, max_lines, ae_list, cp_list)


def _parse_fichier_nat_ae(output_file: str, annee: int, ae_list: dict) -> list[dict]:
    series = pandas.Series({f"{FinancialAe.annee.key}": annee})
    columns_names = FinancialAe.get_columns_fichier_nat_ae()
    index_last_col = len(columns_names) - 1
    columns_types = FinancialAe.get_columns_type_fichier_nat_ae()

    data_chunk = get_data_chunk(output_file, columns_names, columns_types)
    for chunk in data_chunk:
        for i, line in chunk.iterrows():
            line["data_source"] = "NATION"
            # clean la première et dernière ligne qui contient un "
            line[columns_names[0]] = line[columns_names[0]].replace('"', "")
            line[columns_names[index_last_col]] = line[columns_names[index_last_col]].replace('"', "")
            line["source_region"] = get_code_region_by_code_comp(line["societe"])
            key = f"national_{line['source_region']}_{annee}_{line[FinancialAe.n_ej.key]}_{line[FinancialAe.n_poste_ej.key]}"
            ae = pandas.concat([line, series]).to_json()
            if key not in ae_list:
                ae_list[key] = {"ae": [], "cp": []}
            ae_list[key]["ae"].append(ae)
    return ae_list


def _parse_fichier_nat_cp(
    output_file: str, annee: int, chunk_index: int, max_lines: int, ae_list: dict, cp_list: dict
) -> list[dict]:
    columns_names = FinancialCp.get_columns_fichier_nat_cp()
    index_last_col = len(columns_names) - 1
    columns_types = FinancialCp.get_columns_types_fichier_nat_cp()

    data_chunk = get_data_chunk(output_file, columns_names, columns_types)
    for chunk in data_chunk:
        for i, line in chunk.iterrows():
            line["data_source"] = "NATION"
            # clean la première et dernière ligne qui contient un "
            line[columns_names[0]] = line[columns_names[0]].replace('"', "")
            line[columns_names[index_last_col]] = line[columns_names[index_last_col]].replace('"', "")
            line["source_region"] = get_code_region_by_code_comp(line["societe"])
            key = f"national_{line['source_region']}_{annee}_{line[FinancialAe.n_ej.key]}_{line[FinancialAe.n_poste_ej.key]}"
            if key in ae_list.keys():
                ae_list[key]["cp"] += [
                    {
                        "data": line.to_json(),
                        "task": LineImportTechInfo(current_task.request.id, (chunk_index - 1) * max_lines + i),
                    },
                ]
            else:
                cp_list[f"{(chunk_index - 1) * max_lines + i}"] = {
                    "data": line.to_json(),
                    "task": LineImportTechInfo(current_task.request.id, (chunk_index - 1) * max_lines + i),
                }
    return ae_list, cp_list


def _parse_file_ae(output_file: str, source_region: str, annee: int, ae_list: dict) -> list[dict]:
    series = pandas.Series({f"{FinancialAe.annee.key}": annee, f"{FinancialAe.source_region.key}": source_region})
    columns_names = FinancialAe.get_columns_files_ae()
    columns_types = {"programme": str, "n_ej": str, "n_poste_ej": int, "fournisseur_titulaire": str, "siret": str}

    data_chunk = get_data_chunk(output_file, columns_names, columns_types)
    for chunk in data_chunk:
        for i, line in chunk.iterrows():
            line["data_source"] = "REGION"
            key = f"regional_{source_region}_{annee}_{line[FinancialAe.n_ej.key]}_{line[FinancialAe.n_poste_ej.key]}"
            ae = pandas.concat([line, series]).to_json()
            if key not in ae_list:
                ae_list[key] = {"ae": [], "cp": []}
            ae_list[key]["ae"].append(ae)
    return ae_list


def _parse_file_cp(
    output_file: str, source_region: str, annee: int, chunk_index: int, max_lines: int, ae_list: dict, cp_list: dict
) -> list[dict]:
    columns_names = FinancialCp.get_columns_files_cp()
    columns_types = str

    data_chunk = get_data_chunk(output_file, columns_names, columns_types)
    for chunk in data_chunk:
        for i, line in chunk.iterrows():
            line["data_source"] = "REGION"
            key = f"regional_{source_region}_{annee}_{line[FinancialAe.n_ej.key]}_{line[FinancialAe.n_poste_ej.key]}"
            if key in ae_list.keys():
                ae_list[key]["cp"] += [
                    {
                        "data": line.to_json(),
                        "task": LineImportTechInfo(current_task.request.id, (chunk_index - 1) * max_lines + i),
                    },
                ]
            else:
                cp_list[f"{(chunk_index - 1) * max_lines + i}"] = {
                    "data": line.to_json(),
                    "task": LineImportTechInfo(current_task.request.id, (chunk_index - 1) * max_lines + i),
                }
    return ae_list, cp_list


def get_data_chunk(output_file, columns_names, columns_types):
    return pandas.read_csv(
        output_file,
        sep=",",
        header=0,
        names=columns_names,
        dtype=columns_types,
        chunksize=1000,
        keep_default_na=False,
        na_values=[],
        converters={"tax_numb": str},
    )


@celery.task(bind=True, name="split_csv_files_and_run_task")
def split_csv_files_and_run_task(self, fichier: str, task_name: str, csv_options: str, **kwargs):
    max_lines = current_app.config.get("SPLIT_FILE_LINE", DEFAULT_MAX_ROW)
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


@celery.task(bind=True, name="raise_watcher_exception")
def raise_watcher_exception(self, error_message):
    logging.error(error_message)
    raise Exception(error_message)
