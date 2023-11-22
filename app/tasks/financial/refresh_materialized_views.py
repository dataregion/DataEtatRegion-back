from celery import Celery
from app import celeryapp, db
from sqlalchemy import text

celery: Celery = celeryapp.celery


@celery.task(bind=True, name="visuterritoire_maj_materialized_view")
def refresh_materialized_views(self):
    refresh_request = text(
        "refresh materialized view flatten_ademe;"
        "refresh materialized view flatten_ae;"
        "refresh materialized view financial_lines;"
        # Vues visuterritoire
        "refresh materialized view vt_flatten_summarized_ademe;"
        "refresh materialized view vt_flatten_summarized_ae;"
        "refresh materialized view vt_budget_summary;"
        "refresh materialized view vt_m_summary_annee_geo_type_bop;"
        "refresh materialized view vt_m_montant_par_niveau_bop_annee_type;"
    )

    db.session.execute(refresh_request)
    db.session.commit()
