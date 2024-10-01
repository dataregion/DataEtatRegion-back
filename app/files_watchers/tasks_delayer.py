import logging


logger = logging.getLogger(__name__)


def delay_import_fichier_nat(file_path):
    """Appelle la tâche Celery pour importer le fichier."""
    try:
        from app.tasks.financial.import_financial import import_fichier_nat

        task = import_fichier_nat.delay(file_path)
        logger.info(
            f"Demande d'import du fichier national faite. (Tâche asynchrone id {task.id}), file_path : {file_path}"
        )
    except Exception as e:
        logger.error(f"Erreur lors de l'appel de la tâche Celery: {e}")


def delay_raise_watcher_exception(error_message):
    """Appelle une tâche Celery pour lever une exception."""
    logger.error(error_message)
    try:
        from app.tasks.financial.import_financial import raise_watcher_exception

        task = raise_watcher_exception.delay(error_message)
        logger.info(f"Tâche Celery déclenchée pour lever une exception: (Tâche asynchrone id {task.id}).")
    except Exception as e:
        logger.error(f"Erreur lors de l'appel de la tâche Celery: {e}")
