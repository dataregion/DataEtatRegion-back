from typing import List
from celery import Celery
from app import celeryapp, db
from models.entities.financial import Ademe, FinancialAe, FinancialCp
from models.entities.refs import Siret
from models.value_objects.redis_events import MAT_VIEWS_REFRESHED_EVENT_CHANNEL, MaterializedViewsRefreshed
from models.value_objects.audit import RefreshMaterializedViewsEvent
from sqlalchemy import desc, func, text

from models.entities.audit.AuditRefreshMaterializedViewsEvents import (
    AuditRefreshMaterializedViewsEvents,
)

import time
import logging
from datetime import datetime, timezone
from app.clients.redis.factory import make_or_get_redis_client

celery: Celery = celeryapp.celery

_logger = logging.getLogger(__name__)


class LastRefreshMaterializedViewTooRecent(Exception):
    def __init__(self, message="Le dernier refresh materialized view est trop récent"):
        self.message = message
        super().__init__(self.message)


@celery.task(bind=True, name="maj_materialized_view")
def maj_materialized_views(self):
    """
    TODO : désactivation du refresh des vues de Visu Territoire par manque de perf pour le moment
    """
    ffl_deps = [
        ("Ademe", Ademe.Ademe.updated_at),
        ("FinancialAe", FinancialAe.FinancialAe.updated_at),
        ("FinancialCp", FinancialCp.FinancialCp.updated_at),
        ("Siret", Siret.updated_at),
    ]
    view_dependencies = {
        # "vt_flatten_summarized_ademe": [("Ademe", Ademe.Ademe.updated_at)],
        # "vt_budget_summary": [("Ademe", Ademe.Ademe.updated_at), ("FinancialAe", FinancialAe.FinancialAe.updated_at)],
        # "vt_m_summary_annee_geo_type_bop": [
        #     ("Ademe", Ademe.Ademe.updated_at),
        #     ("FinancialAe", FinancialAe.FinancialAe.updated_at),
        # ],
        # "vt_m_montant_par_niveau_bop_annee_type": [
        #     ("Ademe", Ademe.Ademe.updated_at),
        #     ("FinancialAe", FinancialAe.FinancialAe.updated_at),
        # ],
        # "vt_flatten_summarized_ae": [("FinancialAe", FinancialAe.FinancialAe.updated_at)],
        "flatten_financial_lines": ffl_deps,
        "superset_lignes_financieres_52": ffl_deps,
    }

    _logger.debug("Get Last date updated views")
    last_date_update_view = {view: _get_last_refresh_materialized_view_event(view) for view in view_dependencies}

    max_updated_ats = {}
    for deps in view_dependencies.values():
        for label, col in deps:
            if label not in max_updated_ats:
                _logger.debug(f"Get Last date updated for {col}")
                max_updated_ats[label] = db.session.query(func.max(col)).scalar()

    views_to_refresh = []

    for view, dependencies in view_dependencies.items():
        last_refresh: AuditRefreshMaterializedViewsEvents = last_date_update_view[view]
        if last_refresh is None:
            _logger.debug(f"Do refresh {view} (never refreshed)")
            views_to_refresh.append(view)
            continue

        for label, _ in dependencies:
            if max_updated_ats[label] is not None and max_updated_ats[label].astimezone(
                timezone.utc
            ) > last_refresh.date.astimezone(timezone.utc):
                _logger.debug(f"Do refresh {view} (update in {label})")
                views_to_refresh.append(view)
                break

    if views_to_refresh:
        _do_maj_materialized_views(views_to_refresh)

        try:
            msg = MaterializedViewsRefreshed(type="materialized_views_refreshed").model_dump_json()
            make_or_get_redis_client().publish(MAT_VIEWS_REFRESHED_EVENT_CHANNEL, msg)
        except Exception as e:
            _logger.error(
                "Erreur lors de la publication de l'événement de rafraîchissement des vues matérialisées", exc_info=e
            )


def _get_last_refresh_materialized_view_event(view: str) -> datetime | None:
    """
    Retourne la date de dernier refresh d'une vue
    """
    last = (
        db.session.query(AuditRefreshMaterializedViewsEvents)
        .where(AuditRefreshMaterializedViewsEvents.table == view)
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
