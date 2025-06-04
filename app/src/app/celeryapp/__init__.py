from celery import Celery
from kombu import Queue

CELERY_TASK_LIST = ["app.tasks.demarches", "app.tasks.tags"]

db_session = None
celery: Celery = None


def create_celery_app(_app=None) -> Celery:
    """
    Create a new Celery object and tie together the Celery config to the app's config.

    Wrap all tasks in the context of the Flask application.

    :param _app: Flask app
    :return: Celery app
    """
    # New Relic integration
    # if os.environ.get('NEW_RELIC_CELERY_ENABLED') == 'True':
    #     _app.initialize('celery')

    celery = Celery(
        _app.import_name,
        backend=_app.config["result_backend"] if "result_backend" in _app.config else None,
        broker=_app.config["CELERY_BROKER_URL"] if "CELERY_BROKER_URL" in _app.config else None,
        include=CELERY_TASK_LIST,
    )
    celery.conf.update(_app.config)
    celery.conf.task_queues = (
        Queue("file"),
        Queue("line"),
    )

    celery.conf.task_routes = [
        {
            "import_file_*": {"queue": "file"},
            "update_all_siret_task": {"queue": "file"},
            "update_all_tags": {"queue": "file"},
            "update_all_tags_of_ae": {"queue": "line"},
            "update_all_tags_of_cp": {"queue": "line"},
            "update_demarches": {"queue": "file"},
            "update_demarche": {"queue": "line"},
            "share_*": {"queue": "line"},
            "import_line_*": {"queue": "line"},
            "import_lines_*": {"queue": "line"},
            "update_siret_*": {"queue": "line"},
            "apply_tags_*": {"queue": "line"},
            "put_tags_*": {"queue": "file"},
            "update_one_fifth_of_sirets": {"queue": "file"},
            "maj_materialized_view": {"queue": "file"},
            "update_link_*": {"queue": "file"},
            "split_csv_*": {"queue": "file"},
            "read_csv_*": {"queue": "file"},
            "sync_referentiels_with_grist": {"queue": "file"},
            "delayed_inserts": {"queue": "file"},
            "raise_watcher_exception": {"queue": "file"},
        }
    ]

    TaskBase = celery.Task

    class ContextTask(TaskBase):
        abstract = True

        def __call__(self, *args, **kwargs):
            with _app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)

    celery.Task = ContextTask
    return celery
