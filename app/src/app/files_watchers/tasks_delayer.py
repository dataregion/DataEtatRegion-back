import json
import logging
import os
from app import db
from models.entities.audit.AuditUpdateData import AuditUpdateData
from models.value_objects.common import DataType

logger = logging.getLogger(__name__)


def delay_import_fichier_nat(ae_path, cp_path):
    """Appelle la tâche Celery pour importer le fichier."""
    try:
        from app.tasks.files.file_task import read_csv_and_import_fichier_nat_ae_cp

        csv_options = json.dumps({"sep": "|", "skiprows": 0, "keep_default_na": False, "na_values": [], "dtype": "str"})

        read_csv_and_import_fichier_nat_ae_cp.delay(ae_path, cp_path, csv_options)

        # Historique de chargement des données
        db.session.add(
            AuditUpdateData(
                username="sftp_watcher",
                filename=os.path.basename(ae_path),
                data_type=DataType.FINANCIAL_DATA_AE,
            )
        )
        db.session.add(
            AuditUpdateData(
                username="sftp_watcher",
                filename=os.path.basename(cp_path),
                data_type=DataType.FINANCIAL_DATA_CP,
            )
        )
        db.session.commit()
        logger.info(f"*** Demande d'import du fichier national faite. (ae_path : {ae_path}, cp_path : {cp_path}")
    except Exception as e:
        logger.error(f"Erreur lors de l'appel de la tâche Celery: {e}")


def delay_raise_watcher_exception(error_message):
    """Appelle une tâche Celery pour lever une exception."""
    logger.error(error_message)
    try:
        from app.tasks.files.file_task import raise_watcher_exception

        task = raise_watcher_exception.delay(error_message)
        logger.info(f"Tâche Celery déclenchée pour lever une exception: (Tâche asynchrone id {task.id}).")
    except Exception as e:
        logger.error(f"Erreur lors de l'appel de la tâche Celery: {e}")
