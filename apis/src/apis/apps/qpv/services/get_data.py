import asyncio
from apis.apps.qpv.models.chart_data import ChartData
from apis.apps.qpv.models.dashboard_data import DashboardData
from apis.apps.qpv.models.map_data import MapData, QpvData
from models.entities.financial.query.FlattenFinancialLinesDataQpv import FlattenFinancialLinesDataQPV
from models.schemas.financial import FlattenFinancialLinesDataQpvSchema

from services.qpv.query_builder import QpvQueryBuilder
from services.qpv.query_params import QpvQueryParams
from services.shared.source_query_builder import SourcesQueryBuilder
from services.shared.source_query_params import SourcesQueryParams
from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session

from services.regions import get_request_regions, sanitize_source_region_for_bdd_request
from services.utilities.observability import (
    gauge_of_currently_executing,
    summary_of_time,
)
from models.utils import convert_exception

from services.qpv.colonnes import get_list_colonnes_tableau
from apis.shared.exceptions import NoCurrentRegion


app_layer_sanitize_region = convert_exception(ValueError, NoCurrentRegion)(sanitize_source_region_for_bdd_request)


def _to_enriched_ffl(data):
    _loaded = data
    if isinstance(data, FlattenFinancialLinesDataQPV):
        return data
    _loaded: FlattenFinancialLinesDataQPV = FlattenFinancialLinesDataQpvSchema().load(data)
    return _loaded


def _get_query_builder(
    db: Session,
    params: QpvQueryParams,
    additionnal_source_region: str | None = None,
) -> QpvQueryBuilder:
    """
    Recherche la ligne budgetaire selon son ID et sa source region
    """
    print(params.source_region)
    print(params.data_source)
    source_region = app_layer_sanitize_region(params.source_region, params.data_source)
    assert source_region is not None
    _regions = get_request_regions(source_region)

    # On requête toutes les colonnes
    params = params.model_copy(update={"colonnes": ",".join([c.code for c in get_list_colonnes_tableau()])})
    assert "id" in [c for c in params.colonnes.split(",")]

    builder = (
        QpvQueryBuilder(db, params)
        .code_programme_in(params.code_programme_list)
        .code_programme_not_in(params.not_code_programme_list)
        .annee_in(params.annee_list)
        .where_geo_loc_qpv(params.niveau_geo, params.code_geo_list, source_region)
        .lieu_action_code_qpv_in(params.code_qpv_list, source_region)
        .centres_couts_in(params.centres_couts_list)
        .themes_in(params.theme_list)
        .beneficiaire_siret_in(params.beneficiaire_code_list)
        .categorie_juridique_in(
            params.beneficiaire_categorieJuridique_type_list,
            includes_none=params.beneficiaire_categorieJuridique_type_list is not None
            and "autres" in params.beneficiaire_categorieJuridique_type_list,
        )
        .source_region_in(_regions)
    )

    if additionnal_source_region:
        _sanitized = app_layer_sanitize_region(additionnal_source_region)
        assert _sanitized is not None
        _regions.append(_sanitized)
        builder = builder.source_region_in([_sanitized], can_be_null=False)

    return builder


@gauge_of_currently_executing()
@summary_of_time()
def get_lignes(
    db: Session,
    params: QpvQueryParams,
    additionnal_source_region: str | None = None,
):
    """
    Recherche la ligne budgetaire selon son ID et sa source region
    """
    builder = _get_query_builder(db, params, additionnal_source_region)

    # Pagination et récupération des données
    builder = builder.paginate()
    data, has_next = builder.select_all()

    return [_to_enriched_ffl(x) for x in data], has_next


def get_annees_qpv(db: Session, params: SourcesQueryParams):
    params = params.model_copy(
        update={"source_region": app_layer_sanitize_region(params.source_region, params.data_source)}
    )
    assert params.source_region is not None
    _regions = get_request_regions(params.source_region)

    builder = (
        SourcesQueryBuilder(FlattenFinancialLinesDataQPV, db, params)
        .select_custom_model_properties([distinct(FlattenFinancialLinesDataQPV.annee).label("annee")])
        .source_region_in(_regions)
        .data_source_is(params.data_source)
    )
    data, has_next = builder.select_all()
    return [item["annee"] for item in data]


@gauge_of_currently_executing()
@summary_of_time()
async def get_map_data(
    db: Session,
    params: QpvQueryParams,
) -> MapData:
    query_builder = _get_query_builder(db, params)

    qb = query_builder.with_selection(
        [
            FlattenFinancialLinesDataQPV.lieu_action_code_qpv.label("code_qpv"),
            func.coalesce(func.sum(FlattenFinancialLinesDataQPV.montant_ae), 0.0).label("total"),
        ]
    )
    qb._query = qb._query.group_by(FlattenFinancialLinesDataQPV.lieu_action_code_qpv)
    rows = qb._session.execute(qb._query).all()
    return MapData(data=[QpvData(qpv=r.code_qpv, montant=float(r.total or 0)) for r in rows])


@gauge_of_currently_executing()
@summary_of_time()
async def get_dashboard_data(
    db: Session,
    params: QpvQueryParams,
) -> DashboardData:
    query_builder = _get_query_builder(db, params)
    results = await asyncio.gather(
        _get_big_numbers(query_builder),
        _get_pie_chart_themes(query_builder),
        _get_pie_chart_types_porteur(query_builder),
        _get_bar_chart_financeurs(query_builder),
        _get_line_chart_annees(query_builder),
    )
    return DashboardData(
        total_financements=results[0]["total_financements"],
        total_actions=results[0]["total_actions"],
        total_porteurs=results[0]["total_porteurs"],
        pie_chart_themes=results[1],
        pie_chart_types_porteurs=results[2],
        bar_chart_financeurs=results[3],
        line_chart_annees=results[4],
    )


async def _get_big_numbers(query_builder: QpvQueryBuilder):
    # Total des montants
    query_total_financements = query_builder.with_selection(
        select(func.coalesce(func.sum(FlattenFinancialLinesDataQPV.montant_ae), 0.0))
    )
    total_financements = query_total_financements.select_one()
    # Nombres d'AE
    query_total_actions = query_builder.with_selection(
        select(func.coalesce(func.count(func.distinct(FlattenFinancialLinesDataQPV.id)), 0.0))
    )
    total_actions = query_total_actions.select_one()
    # Nombre de bénéficiaires
    query_total_porteurs = query_builder.with_selection(
        select(func.coalesce(func.count(func.distinct(FlattenFinancialLinesDataQPV.beneficiaire_code)), 0.0))
    )
    total_porteurs = query_total_porteurs.select_one()

    return {
        "total_financements": total_financements,
        "total_actions": total_actions,
        "total_porteurs": total_porteurs,
    }


async def _get_pie_chart_themes(query_builder: QpvQueryBuilder):
    qb = query_builder.with_selection(
        [
            FlattenFinancialLinesDataQPV.programme_theme.label("theme"),
            func.coalesce(func.sum(FlattenFinancialLinesDataQPV.montant_ae), 0.0).label("total"),
        ]
    )
    qb._query = qb._query.group_by(None).group_by(FlattenFinancialLinesDataQPV.programme_theme)
    rows = qb._session.execute(qb._query).all()
    return ChartData(labels=[str(r.theme) for r in rows], values=[float(r.total or 0) for r in rows])


async def _get_pie_chart_types_porteur(query_builder: QpvQueryBuilder):
    qb = query_builder.with_selection(
        [
            FlattenFinancialLinesDataQPV.beneficiaire_categorieJuridique_type.label("type_porteur"),
            func.coalesce(func.sum(FlattenFinancialLinesDataQPV.montant_ae), 0.0).label("total"),
        ]
    )
    qb._query = qb._query.group_by(None).group_by(FlattenFinancialLinesDataQPV.beneficiaire_categorieJuridique_type)
    rows = qb._session.execute(qb._query).all()
    return ChartData(labels=[str(r.type_porteur) for r in rows], values=[float(r.total or 0) for r in rows])


async def _get_bar_chart_financeurs(query_builder: QpvQueryBuilder):
    qb = query_builder.with_selection(
        [
            FlattenFinancialLinesDataQPV.centreCouts_description.label("financeur"),
            func.coalesce(func.sum(FlattenFinancialLinesDataQPV.montant_ae), 0.0).label("total"),
        ]
    )
    qb._query = qb._query.group_by(None).group_by(FlattenFinancialLinesDataQPV.centreCouts_description)
    rows = qb._session.execute(qb._query).all()
    return ChartData(labels=[str(r.financeur) for r in rows], values=[float(r.total or 0) for r in rows])


async def _get_line_chart_annees(query_builder: QpvQueryBuilder):
    qb = query_builder.with_selection(
        [
            FlattenFinancialLinesDataQPV.annee.label("annee"),
            func.coalesce(func.sum(FlattenFinancialLinesDataQPV.montant_ae), 0.0).label("total"),
        ]
    )
    qb._query = qb._query.group_by(None).group_by(FlattenFinancialLinesDataQPV.annee)
    rows = qb._session.execute(qb._query).all()
    return ChartData(labels=[str(r.annee) for r in rows], values=[float(r.total or 0) for r in rows])


async def _get_line_chart_annees(query_builder: QpvQueryBuilder):
    qb = query_builder.with_selection(
        [
            FlattenFinancialLinesDataQPV.annee.label("annee"),
            func.coalesce(func.sum(FlattenFinancialLinesDataQPV.montant_ae), 0.0).label("total"),
        ]
    )
    qb._query = qb._query.group_by(None).group_by(FlattenFinancialLinesDataQPV.annee)
    qb._query = qb._query.order_by(None).order_by(FlattenFinancialLinesDataQPV.annee)
    rows = qb._session.execute(qb._query).all()
    return ChartData(labels=[str(int(r.annee)) for r in rows], values=[float(r.total or 0) for r in rows])
