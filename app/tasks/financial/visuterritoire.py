from . import logger

from celery import Celery
from app import celeryapp, db
from sqlalchemy import text

celery: Celery = celeryapp.celery


@celery.task(bind=True, name="visuterritoire_maj_materialized_view")
def refresh_materialized_views(self):
    refresh_request = text(
        "refresh materialized view flatten_summarized_ae;"
        "refresh materialized view budget_summary;"
        "refresh materialized view m_summary_annee_geo_type_bop;"
        "refresh materialized view m_montant_par_niveau_bop_annee_type;"
    )

    db.session.execute(refresh_request)
    db.session.commit()
