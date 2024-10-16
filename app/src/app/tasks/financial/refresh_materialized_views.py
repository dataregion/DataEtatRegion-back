from celery import Celery
from app import celeryapp, db
from sqlalchemy import desc, text

from app.models.audit.AuditRefreshMaterializedViewsEvents import (
    AuditRefreshMaterializedViewsEvents,
    RefreshMaterializedViewsEvent,
)

import time
import logging
from datetime import datetime, timedelta, timezone

celery: Celery = celeryapp.celery

_logger = logging.getLogger(__name__)

_safety_timedelta = timedelta(hours=6)


class LastRefreshMaterializedViewTooRecent(Exception):
    def __init__(self, message="Le dernier refresh materialized view est trop récent"):
        self.message = message
        super().__init__(self.message)


@celery.task(bind=True, name="maj_materialized_view")
def maj_materialized_views(self):
    _check_refresh_materialized_view_event()
    _do_maj_materialized_views(self)


def _check_refresh_materialized_view_event():
    """Vérifie que le dernier evenement de rafraichissement de vues materialisée date d'au moins quelques heures"""
    last = (
        db.session.query(AuditRefreshMaterializedViewsEvents)
        .order_by(desc(AuditRefreshMaterializedViewsEvents.date))
        .first()
    )

    if not last:
        return

    six_hours_ago = datetime.now(timezone.utc) - _safety_timedelta
    last_date: datetime = last.date  # type: ignore

    if last_date > six_hours_ago:
        _logger.warning(
            "Durant le rafraichissement des vues materialisées "
            "Le dernier rafraichissement date d'il y a moins de six heure. "
            "On ne rafraichit pas !"
        )
        raise LastRefreshMaterializedViewTooRecent()


def _do_maj_materialized_views(self):
    begin_evt = AuditRefreshMaterializedViewsEvents.create(RefreshMaterializedViewsEvent.BEGIN)
    db.session.add(begin_evt)
    db.session.commit()

    views = [
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
        _logger.info(f"Refresh materialized view {view}")
        db.session.execute(text(f"refresh materialized view {view};"))
        db.session.commit()
        elapsed = time.time() - start
        _logger.info(f"--- refreshed materialized view {view} in {elapsed} seconds")
        result[view] = {"elapsed_seconds": elapsed}

    ended_evt = AuditRefreshMaterializedViewsEvents.create(RefreshMaterializedViewsEvent.ENDED)
    db.session.add(ended_evt)
    db.session.commit()

    return result
