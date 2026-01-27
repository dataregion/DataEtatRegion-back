from datetime import datetime
import os
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


IMPORT_DIR = get_config().dossier_des_imports


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
def process_chunk(chunk, chunk_index: int, schema: ImportQpvLieuActionSchema):
    flow_run_id = runtime.flow_run.id
    values: list[dict] = []

    # Validation soft, ligne par ligne
    valid_rows, invalid_rows = schema.validate_rows(chunk)

    _print(f"[CHUNK {chunk_index}] {len(valid_rows)} lignes valides à traiter.")
    if not invalid_rows.empty:
        _print(f"[CHUNK {chunk_index}] {len(invalid_rows)} lignes invalides ignorées.")

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
    _print(f"Start for file : {fichier}")

    _print(f"Validation header : {fichier}")
    schema = ImportQpvLieuActionSchema()
    schema.validate_header(fichier, sep=separateur)

    chunks = pd.read_csv(
        fichier,
        sep=separateur,
        header=0,
        keep_default_na=False,
        dtype=schema.pandas_dtypes(),
        chunksize=1000,
    )
    total = 0
    for idx, chunk in enumerate(chunks):
        total += process_chunk(chunk, idx, schema)

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    move_folder = os.path.join(IMPORT_DIR, "save", timestamp)
    _print(f"Move file {fichier} -> {move_folder}")
    os.makedirs(move_folder, exist_ok=True)
    shutil.move(fichier, move_folder)

    _print(f"End : lignes importées : {total}")
    return total
