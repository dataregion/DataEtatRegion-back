from datetime import datetime, timedelta, timezone
from app.tasks.financial.refresh_materialized_views import maj_materialized_views
from models.entities.audit.AuditRefreshMaterializedViewsEvents import AuditRefreshMaterializedViewsEvents
from models.entities.financial.Ademe import Ademe
from models.entities.financial.FinancialAe import FinancialAe
from models.entities.financial.FinancialCp import FinancialCp
from models.entities.refs import Siret
from models.value_objects.audit import RefreshMaterializedViewsEvent
from tests.tasks.tags.test_tag_acv import add_references
import pytest
from . import build_ademe, build_financial_ae, build_financial_cp, build_siret


def _build_audit(
    session,
    views={
        # "vt_flatten_summarized_ademe",
        # "vt_budget_summary",
        # "vt_m_summary_annee_geo_type_bop",
        # "vt_m_montant_par_niveau_bop_annee_type",
        # "vt_flatten_summarized_ae",
        "flatten_financial_lines",
        "superset_lignes_financieres_52",
    },
):
    for view in views:
        session.add(AuditRefreshMaterializedViewsEvents.create(RefreshMaterializedViewsEvent.BEGIN, view))


@pytest.fixture(scope="function", autouse=True)
def cleanup_after_tests(database):
    yield
    # Exécutez des actions nécessaires après tous les tests
    database.session.execute(database.delete(Ademe))
    database.session.execute(database.delete(FinancialAe))
    database.session.execute(database.delete(FinancialCp))
    database.session.execute(database.delete(Siret))
    database.session.execute(database.delete(AuditRefreshMaterializedViewsEvents))
    database.session.commit()


def test_refresh_no_data_updated_and_no_refresh(database, session):
    """
    Test le cas où pas de données insérés et zéro refresh de vue effectué
    """
    maj_materialized_views()

    events = (
        session.execute(
            database.select(AuditRefreshMaterializedViewsEvents).where(
                AuditRefreshMaterializedViewsEvents.event == RefreshMaterializedViewsEvent.ENDED
            )
        )
        .scalars()
        .all()
    )

    assert len(events) == 2
    tables_with_events = {e.table for e in events}
    assert "flatten_financial_lines" in tables_with_events


def test_refresh_no_data_updated_refresh_exist(database, session):
    """
    Test le cas où pas de données insérés et les refresh ont déjà été fait
    """
    # GIVEN
    _build_audit(session)
    session.commit()

    # DO
    maj_materialized_views()

    events = (
        session.execute(
            database.select(AuditRefreshMaterializedViewsEvents).where(
                AuditRefreshMaterializedViewsEvents.event == RefreshMaterializedViewsEvent.ENDED
            )
        )
        .scalars()
        .all()
    )

    assert len(events) == 0


def test_maj_materialized_views_no_refresh_need(database, session):
    """
    Test le cas où les données sont toutes plus anciennes que le refresh des vues
    """
    # GIVEN
    j_minus_2 = datetime.now(timezone.utc) - timedelta(days=2)

    session.add(build_siret(j_minus_2))
    ademe = build_ademe(j_minus_2)
    add_references(ademe, session, region="53")
    session.add(ademe)

    fcp = build_financial_cp(j_minus_2)
    add_references(fcp, session, region="53")
    session.add(fcp)

    fae = build_financial_ae(j_minus_2)
    add_references(fae, session, region="53")
    session.add(fae)
    # ajoute un audit pour toutes les vues
    _build_audit(session)
    session.commit()

    # DO
    maj_materialized_views()

    # ASSERT
    events = (
        session.execute(
            database.select(AuditRefreshMaterializedViewsEvents).where(
                AuditRefreshMaterializedViewsEvents.event == RefreshMaterializedViewsEvent.ENDED
            )
        )
        .scalars()
        .all()
    )
    assert len(events) == 0


def test_need_ademe_maj(database, session):
    """
    Test le cas où les données sont toutes plus anciennes que le refresh des vues
    """
    # GIVEN
    j_minus_2 = datetime.now(timezone.utc) - timedelta(days=2)
    j_plus_1 = datetime.now(timezone.utc) + timedelta(days=1)

    session.add(build_siret(j_minus_2))

    # Ademe mis à jours a +1
    ademe = build_ademe(j_plus_1)
    add_references(ademe, session, region="53")
    session.add(ademe)

    fcp = build_financial_cp(j_minus_2)
    add_references(fcp, session, region="53")
    session.add(fcp)

    fae = build_financial_ae(j_minus_2)
    add_references(fae, session, region="53")
    session.add(fae)
    # ajoute un audit pour toutes les vues
    _build_audit(session)
    session.commit()

    # DO
    maj_materialized_views()

    # ASSERT
    events = (
        session.execute(
            database.select(AuditRefreshMaterializedViewsEvents).where(
                AuditRefreshMaterializedViewsEvents.event == RefreshMaterializedViewsEvent.ENDED
            )
        )
        .scalars()
        .all()
    )
    assert len(events) == 2


def test_only_siret_maj(database, session):
    """
    Test le cas où uniquement les sirets sont maj
    """
    # GIVEN
    j_minus_2 = datetime.now(timezone.utc) - timedelta(days=2)
    j_plus_1 = datetime.now(timezone.utc) + timedelta(days=1)

    # Siret mis à jours a +1
    session.add(build_siret(j_plus_1))

    ademe = build_ademe(j_minus_2)
    add_references(ademe, session, region="53")
    session.add(ademe)

    fcp = build_financial_cp(j_minus_2)
    add_references(fcp, session, region="53")
    session.add(fcp)

    fae = build_financial_ae(j_minus_2)
    add_references(fae, session, region="53")
    session.add(fae)
    # ajoute un audit pour toutes les vues
    _build_audit(session)
    session.commit()

    # DO
    maj_materialized_views()

    # ASSERT
    events = (
        session.execute(
            database.select(AuditRefreshMaterializedViewsEvents).where(
                AuditRefreshMaterializedViewsEvents.event == RefreshMaterializedViewsEvent.ENDED
            )
        )
        .scalars()
        .all()
    )
    assert len(events) == 2
    tables_with_events = {e.table for e in events}
    assert "flatten_financial_lines" in tables_with_events


def test_only_financial_ae_cp_maj(database, session):
    """
    Test le cas où uniquement les AE et CP sont updates
    """
    # GIVEN
    j_minus_2 = datetime.now(timezone.utc) - timedelta(days=2)
    j_plus_1 = datetime.now(timezone.utc) + timedelta(days=1)

    session.add(build_siret(j_minus_2))

    ademe = build_ademe(j_minus_2)
    add_references(ademe, session, region="53")
    session.add(ademe)

    # CP mis à jours a j+1
    fcp = build_financial_cp(j_plus_1)
    add_references(fcp, session, region="53")
    session.add(fcp)

    # AE mis à jours a j+1
    fae = build_financial_ae(j_plus_1)
    add_references(fae, session, region="53")
    session.add(fae)
    # ajoute un audit pour toutes les vues
    _build_audit(session)
    session.commit()

    # DO
    maj_materialized_views()

    # ASSERT
    events = (
        session.execute(
            database.select(AuditRefreshMaterializedViewsEvents).where(
                AuditRefreshMaterializedViewsEvents.event == RefreshMaterializedViewsEvent.ENDED
            )
        )
        .scalars()
        .all()
    )
    assert len(events) == 2
    tables_with_events = {e.table for e in events}
    assert "flatten_financial_lines" in tables_with_events


def test_no_refresh_view_done(database, session):
    """
    Test le cas où des données sont présentes, mais aucun audit refresh realisé
    """
    # GIVEN
    j_minus_2 = datetime.now(timezone.utc) - timedelta(days=2)

    session.add(build_siret(j_minus_2))

    ademe = build_ademe(j_minus_2)
    add_references(ademe, session, region="53")
    session.add(ademe)

    # CP mis à jours a j+1
    fcp = build_financial_cp(j_minus_2)
    add_references(fcp, session, region="53")
    session.add(fcp)

    # AE mis à jours a j+1
    fae = build_financial_ae(j_minus_2)
    add_references(fae, session, region="53")
    session.add(fae)
    session.commit()

    # DO
    maj_materialized_views()

    # ASSERT
    events = (
        session.execute(
            database.select(AuditRefreshMaterializedViewsEvents).where(
                AuditRefreshMaterializedViewsEvents.event == RefreshMaterializedViewsEvent.ENDED
            )
        )
        .scalars()
        .all()
    )
    assert len(events) == 2
    tables_with_events = {e.table for e in events}
    assert "flatten_financial_lines" in tables_with_events
