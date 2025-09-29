from celery.schedules import crontab

RESULT_EXPIRES = None  # Sinon, beat nettoie le result backend

TIMEZONE = "UTC"
CELERYBEAT_SCHEDULE = {
    "importe-ademe-auto": {
        "task": "import_file_ademe_from_website",
        "schedule": crontab(hour=0, minute=0, day_of_month=1),
        "args": ("https://www.data.gouv.fr/fr/datasets/r/e8a06bbd-08bb-448b-b040-2a2666b1e082",),
    },
    "importe-pvd-auto": {
        "task": "import_file_pvd_from_website",
        "schedule": crontab(hour=0, minute=0, day_of_month=1),
        "args": ("https://www.data.gouv.fr/api/1/datasets/r/1fa831ec-d912-4277-8b95-a8b998bf951e",),
    },
    "importe-acv-auto": {
        "task": "import_file_acv_from_website",
        "schedule": crontab(hour=0, minute=0, day_of_month=1),
        "args": ("https://www.data.gouv.fr/api/1/datasets/r/8b6f422b-cbdf-459a-9a16-d6be4b92d91a",),
    },
}
