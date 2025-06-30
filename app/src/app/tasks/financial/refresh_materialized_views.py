from typing import List
from celery import Celery
from app import celeryapp, db
from models.entities.financial import Ademe
from models.value_objects.audit import RefreshMaterializedViewsEvent
from sqlalchemy import desc, func, text

from models.entities.audit.AuditRefreshMaterializedViewsEvents import (
    AuditRefreshMaterializedViewsEvents,
)

import time
import logging
from datetime import datetime, timedelta

celery: Celery = celeryapp.celery

_logger = logging.getLogger(__name__)

_safety_timedelta = timedelta(hours=6)


class LastRefreshMaterializedViewTooRecent(Exception):
    def __init__(self, message="Le dernier refresh materialized view est trop récent"):
        self.message = message
        super().__init__(self.message)


@celery.task(bind=True, name="maj_materialized_view")
def maj_materialized_views(self):
    # FINANCIAL_AE
    # max_updated_at_financial_ae = db.session.query(func.max(FinancialAe.FinancialAe.updated_at)).scalar()

    # last_update_financial_ae = _get_last_refresh_materialized_view_event(FinancialAe.FinancialAe.__tablename__)

    # ADEME
    max_updated_at_ademe = db.session.query(func.max(Ademe.Ademe.updated_at)).scalar()

    last_update_ademe = _get_last_refresh_materialized_view_event(Ademe.Ademe.__tablename__)

    views_to_refresh = []

    ademe_updated = last_update_ademe is None or (max_updated_at_ademe > last_update_ademe)
    # financial_ae_updated = (last_update_financial_ae is None or (max_updated_at_financial_ae > last_update_financial_ae))

    if ademe_updated:
        _logger.info("Ademe to updated")
        views_to_refresh.append("vt_flatten_summarized_ademe")
        views_to_refresh.append("vt_budget_summary")
        views_to_refresh.append("vt_m_summary_annee_geo_type_bop")
        views_to_refresh.append("vt_m_montant_par_niveau_bop_annee_type")

        views_to_refresh.append("flatten_financial_lines")
        views_to_refresh.append("vt_flatten_summarized_ae")

    if len(views_to_refresh) > 0:
        _do_maj_materialized_views(views_to_refresh)


def _get_last_refresh_materialized_view_event(table: str) -> datetime | None:
    """
    Retourne la date de dernier refresh d'une vue
    """
    last = (
        db.session.query(AuditRefreshMaterializedViewsEvents)
        .where(AuditRefreshMaterializedViewsEvents.table == table)
        .order_by(desc(AuditRefreshMaterializedViewsEvents.date))
        .first()
    )

    if not last:
        return None

    return last


def _do_maj_materialized_views(views: List[str]):

    result = {}

    for view in views:
        begin_evt = AuditRefreshMaterializedViewsEvents.create(RefreshMaterializedViewsEvent.BEGIN, view)
        db.session.add(begin_evt)
        db.session.commit()

        start = time.time()
        _logger.info(f"Refresh materialized view {view}")
        db.session.execute(text(f"refresh materialized view {view};"))
        db.session.commit()
        elapsed = time.time() - start
        _logger.info(f"--- refreshed materialized view {view} in {elapsed} seconds")
        result[view] = {"elapsed_seconds": elapsed}

        ended_evt = AuditRefreshMaterializedViewsEvents.create(RefreshMaterializedViewsEvent.ENDED, view)
        db.session.add(ended_evt)
        db.session.commit()

    return result
