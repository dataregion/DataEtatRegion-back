from celery import Celery
from app import celeryapp, db
from sqlalchemy import text
import time

celery: Celery = celeryapp.celery


@celery.task(bind=True, name="maj_materialized_view")
def refresh_materialized_views(self):
    views = [
        "flatten_ademe",
        "flatten_ae",
        "flatten_financial_lines",
        # Vues visuterritoire
        "vt_flatten_summarized_ademe",
        "vt_flatten_summarized_ae",
        "vt_budget_summary",
        "vt_m_summary_annee_geo_type_bop",
        "vt_m_montant_par_niveau_bop_annee_type",
    ]

    result = {}

    for view in views:
        start = time.time()
        db.session.execute(text(f"refresh materialized view {view};"))
        db.session.commit()
        elapsed = time.time() - start

        result[view] = {"elapsed_seconds": elapsed}

    return result
