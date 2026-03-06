from __future__ import annotations

from prefect import flow, task, get_run_logger
from typing import Any, Dict, List


@task
def validate_model_task(referentiel: str) -> None:
    logger = get_run_logger()
    # TODO: vérifier que le modèle existe et hérite de _SyncedWithGrist
    logger.info(f"Validate model for referentiel={referentiel}")


@task
def init_synchro_config_task(referentiel: str, doc_id: str, table_id: str) -> Dict[str, Any]:
    logger = get_run_logger()
    # Créer ou récupérer l'entrée SynchroGrist
    logger.info("Init or get SynchroGrist entry")
    return {"synchro_grist_id": None}


@task
def fetch_grist_records_task(doc_id: str, table_id: str) -> List[Dict[str, Any]]:
    logger = get_run_logger()
    # Utiliser gristcli (via import local) pour récupérer les records
    logger.info(f"Fetch Grist records for doc={doc_id} table={table_id}")
    # TODO: importer et appeler gristcli.gristservices.grist_api.get_records_of_table
    return []


@task
def validate_grist_data_task(records: List[Dict[str, Any]]) -> None:
    logger = get_run_logger()
    # Vérifier que records contient des éléments et que chaque record a fields.code
    logger.info(f"Validate {len(records)} records")


@task
def sync_batch_task(batch: List[Dict[str, Any]], synchro_meta: Dict[str, Any]) -> Dict[str, int]:
    logger = get_run_logger()
    # TODO: implémenter UPSERT par record
    logger.info(f"Syncing batch of {len(batch)} records")
    return {"updated": len(batch)}


@flow
def sync_referentiel_grist_flow(referentiel: str, doc_id: str, table_id: str, batch_size: int = 100):
    logger = get_run_logger()
    logger.info("Start sync_referentiel_grist_flow")

    validate_model_task(referentiel)
    synchro_meta = init_synchro_config_task(referentiel, doc_id, table_id)

    records = fetch_grist_records_task(doc_id, table_id)
    validate_grist_data_task(records)

    # découper en batchs
    for i in range(0, len(records), batch_size):
        batch = records[i : i + batch_size]
        sync_batch_task.submit(batch, synchro_meta)

    logger.info("Flow finished")


if __name__ == "__main__":
    # Exemple d'exécution locale
    sync_referentiel_grist_flow("ref_centre_couts", "<docId>", "<tableId>")
