import logging


logger = logging.getLogger(__name__)


def delay_import_fichier_nat(ae_path, cp_path):
    """Appelle la tâche Celery pour importer le fichier."""
    try:
        from app.tasks.files.file_task import import_fichier_nat_ae_cp

        task = import_fichier_nat_ae_cp.delay(ae_path, cp_path)
        logger.info(
            f"*** Demande d'import du fichier national faite. (Tâche asynchrone id {task.id}), ae_path : {ae_path}, cp_path : {cp_path}"
        )
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
