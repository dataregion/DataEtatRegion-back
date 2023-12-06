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
        "args": ("https://www.data.gouv.fr/fr/datasets/r/2a5a9898-1b6c-457c-b67e-032b0a0c7b8a",),
    },
    "importe-acv-auto": {
        "task": "import_file_acv_from_website",
        "schedule": crontab(hour=0, minute=0, day_of_month=1),
        "args": ("https://www.data.gouv.fr/fr/datasets/r/f547b346-af1e-41b5-b647-8f23e71ffe1c",),
    },
}
