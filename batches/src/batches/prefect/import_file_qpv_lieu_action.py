from datetime import datetime
import os
from pathlib import Path
import shutil
from prefect import flow, task, runtime
import pandas as pd

from services.qpv.files.import_qpv_lieu_action_schema import ImportQpvLieuActionSchema
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert
from batches.config.current import get_config
from batches.database import init_persistence_module, session_scope

init_persistence_module()

from models.entities.financial.QpvLieuAction import QpvLieuAction  # noqa: E402


UPLOAD_FOLDER = get_config().upload_folder
IMPORT_DIR = get_config().dossier_des_imports / "qpv_lieu_action"


def _print(message: str):
    print(f"[IMPORT][QPV_LIEU_ACTION] {message}")


@task(log_prints=True)
def save_qpv_lieu_action(values: list, chunk_index: int):
    stmt = insert(QpvLieuAction).values(values)

    stmt = stmt.on_conflict_do_update(
        index_elements=["annee_exercice", "ref_action", "ej", "code_qpv"],
        set_={
            "siret": stmt.excluded.siret,
            "montant_ventille": stmt.excluded.montant_ventille,
            "libelle_action": stmt.excluded.libelle_action,
            "file_import_taskid": stmt.excluded.file_import_taskid,
            "file_import_lineno": stmt.excluded.file_import_lineno,
        },
    )

    stmt = stmt.returning(QpvLieuAction.id, text("xmax = 0 AS inserted"))

    with session_scope() as session:
        result = session.execute(stmt).all()
        session.commit()

    inserted = sum(1 for _, ins in result if ins)
    updated = len(result) - inserted

    _print(f"[CHUNK {chunk_index}] INSERT={inserted} UPDATE={updated} TOTAL={len(result)}")

    return {
        "inserted": inserted,
        "updated": updated,
        "total": len(result),
    }


@task(log_prints=True)
def process_chunk(valid_rows: pd.DataFrame, chunk_index: int, schema: ImportQpvLieuActionSchema):
    flow_run_id = runtime.flow_run.id
    values: list[dict] = []

    for i, line in enumerate(valid_rows.to_dict(orient="records")):
        lineno = chunk_index * 1000 + i

        # Sélection du code QPV, on privilégie la codification 2024
        code_qpv = None
        if line.get("code_qpv24") and line["code_qpv24"] != "NR":
            code_qpv = line["code_qpv24"]
        elif line.get("code_qpv") and line["code_qpv"] != "NR":
            code_qpv = line["code_qpv"]

        if not code_qpv:
            continue

        row = QpvLieuAction.format_dict(line)
        row["file_import_taskid"] = flow_run_id
        row["file_import_lineno"] = lineno
        values.append(row)

    if values:
        save_qpv_lieu_action(values, chunk_index)

    return len(values)


@flow(log_prints=True)
def import_file_qpv_lieu_action(fichier: str, separateur: str = ","):
    from prefect.settings import PREFECT_API_URL

    print("Prefect API URL (runtime):", PREFECT_API_URL.value())

    _print(f"Start for file : {fichier}")

    _print(f"Validation header : {fichier}")
    schema = ImportQpvLieuActionSchema()

    # Validation hard, check structure, Exception si échoue
    schema.validate_header(fichier, sep=separateur)

    chunks = schema.read_chunks(fichier, sep=separateur, chunksize=1000)

    total = 0
    for idx, chunk in enumerate(chunks):
        # Validation soft, ligne par ligne
        valid_rows, invalid_rows = schema.validate_rows(chunk)

        _print(f"[CHUNK {idx}] {len(valid_rows)} lignes valides à traiter.")
        if not invalid_rows.empty:
            _print(f"[CHUNK {idx}] {len(invalid_rows)} lignes invalides ignorées.")

        valid_rows = schema.cast_valid_rows(valid_rows)

        total += process_chunk(valid_rows, idx, schema)

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    src = Path(fichier)

    folder_historique = UPLOAD_FOLDER / "save" / timestamp
    os.makedirs(folder_historique, exist_ok=True)
    dst = folder_historique / src.name
    _print(f"Copy file (historique) : {src} -> {dst}")
    shutil.copy(src, dst)

    save_folder = IMPORT_DIR
    os.makedirs(save_folder, exist_ok=True)
    dst = save_folder / f"{timestamp}_{src.name}"
    _print(f"Move file : {src} -> {dst}")
    shutil.move(src, dst)

    _print(f"End : lignes importées : {total}")
    return total
