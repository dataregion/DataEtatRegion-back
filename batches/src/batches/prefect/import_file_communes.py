from __future__ import annotations

import shutil
import tempfile
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests
from prefect import flow, get_run_logger, task
from prefect.cache_policies import NO_CACHE

from batches.config.current import get_config
from batches.database import init_persistence_module, session_scope

init_persistence_module()

from services.refs.communes import (  # noqa: E402
    select_communes_id,
    set_communes_acv,
    set_communes_non_acv,
    set_communes_non_pvd,
    set_communes_pvd,
)


def _archive_file(filepath: str, archive_label: str) -> str:
    archive_dir = get_config().dossier_des_imports / "communes"
    archive_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    archived_path = archive_dir / f"{archive_label}_{timestamp}.csv"
    shutil.move(filepath, archived_path)
    return str(archived_path)


def _process_communes_file(
    filepath: str,
    *,
    date_format: str,
    reset_communes,
    update_communes,
    flag_field: str,
    date_field: str,
    import_label: str,
) -> None:
    logger = get_run_logger()
    logger.info("Début de l'import", extra={"filepath": filepath, "import": import_label})

    data_chunk_iter = pd.read_csv(
        filepath,
        sep=",",
        header=0,
        dtype={"insee_com": str, "lib_com": str, "date_signature": str},
        chunksize=1000,
    )

    with session_scope() as session:
        reset_communes(session)

        for chunk in data_chunk_iter:
            dates_by_code: dict[str, str | None] = {}
            for _, row in chunk.iterrows():
                code_commune = row.get("insee_com")
                if pd.notna(code_commune) and code_commune:
                    date_signature = row.get("date_signature")
                    dates_by_code[code_commune] = date_signature if pd.notna(date_signature) else None

            if not dates_by_code:
                continue

            communes = select_communes_id(session, dates_by_code.keys())
            updates_to_commit: list[dict] = []

            for commune_id, code_commune in communes:
                raw_date = dates_by_code.get(code_commune)
                parsed_date = datetime.strptime(raw_date, date_format) if raw_date is not None else None
                updates_to_commit.append(
                    {
                        "id": commune_id,
                        flag_field: True,
                        date_field: parsed_date,
                    }
                )

            if updates_to_commit:
                update_communes(session, updates_to_commit)

    logger.info("Fin de l'import", extra={"filepath": filepath, "import": import_label})


@task(cache_policy=NO_CACHE, retries=3, retry_delay_seconds=30)
def download_file_from_website(url: str) -> str:
    logger = get_run_logger()
    response = requests.get(url, stream=True, timeout=60)
    response.raise_for_status()

    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                temp_file.write(chunk)

    logger.info("Fichier téléchargé", extra={"url": url, "filepath": temp_file.name})
    return temp_file.name


@flow(name="import_file_pvd_from_website", log_prints=True)
def import_file_pvd_from_website(url: str) -> str:
    logger = get_run_logger()
    filepath = download_file_from_website(url)

    try:
        _process_communes_file(
            filepath,
            date_format="%d/%m/%Y",
            reset_communes=set_communes_non_pvd,
            update_communes=set_communes_pvd,
            flag_field="is_pvd",
            date_field="date_pvd",
            import_label="PVD",
        )
        return _archive_file(filepath, "pvd")
    except Exception:
        logger.exception("Erreur lors de l'import PVD", extra={"url": url, "filepath": filepath})
        raise
    finally:
        # Une fois archivé, le fichier n'est plus là : on ne supprime que le téléchargement non archivé
        Path(filepath).unlink(missing_ok=True)


@flow(name="import_file_acv_from_website", log_prints=True)
def import_file_acv_from_website(url: str) -> str:
    logger = get_run_logger()
    filepath = download_file_from_website(url)

    try:
        _process_communes_file(
            filepath,
            date_format="%d-%m-%Y",
            reset_communes=set_communes_non_acv,
            update_communes=set_communes_acv,
            flag_field="is_acv",
            date_field="date_acv",
            import_label="ACV",
        )
        return _archive_file(filepath, "acv")
    except Exception:
        logger.exception("Erreur lors de l'import ACV", extra={"url": url, "filepath": filepath})
        raise
    finally:
        # Une fois archivé, le fichier n'est plus là : on ne supprime que le téléchargement non archivé
        Path(filepath).unlink(missing_ok=True)
