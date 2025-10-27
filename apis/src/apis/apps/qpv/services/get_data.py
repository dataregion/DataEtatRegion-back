import asyncio
from apis.apps.qpv.models.chart_data import ChartData
from apis.apps.qpv.models.dashboard_data import DashboardData
from models.entities.financial.query.FlattenFinancialLinesDataQpv import (
    EnrichedFlattenFinancialLinesDataQPV,
)
from models.schemas.financial import EnrichedFlattenFinancialLinesSchema

from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session

from services.regions import get_request_regions, sanitize_source_region_for_bdd_request
from services.utilities.observability import (
    gauge_of_currently_executing,
    summary_of_time,
)
from models.utils import convert_exception

from apis.apps.qpv.models.qpv_query_params import (
    QpvQueryParams,
    SourcesQueryParams,
)
from apis.apps.qpv.services.get_colonnes import get_list_colonnes_tableau
from apis.apps.qpv.services.query_builder import (
    QpvQueryBuilder,
    SourcesQueryBuilder,
)
from apis.shared.exceptions import NoCurrentRegion


app_layer_sanitize_region = convert_exception(ValueError, NoCurrentRegion)(sanitize_source_region_for_bdd_request)

def _to_enriched_ffl(data):
    _loaded = data
    print(data)
    if isinstance(data, EnrichedFlattenFinancialLinesDataQPV):
        print('no load')
        return data
    _loaded: EnrichedFlattenFinancialLinesDataQPV = EnrichedFlattenFinancialLinesSchema().load(data)
    return _loaded

def _get_query_builder(
    db: Session,
    params: QpvQueryParams,
) -> QpvQueryBuilder:
    
    """
    Recherche la ligne budgetaire selon son ID et sa source region
    """
    print("=============") 
    print("=============")
    source_region = app_layer_sanitize_region(params.source_region, params.data_source)
    print("=============")
    print(source_region)
    assert source_region is not None
    _regions = get_request_regions(source_region)

    # On requête toutes les colonnes
    params.colonnes = [c.code for c in get_list_colonnes_tableau()]
    params.colonnes.append("id")

    builder = (
        QpvQueryBuilder(db, params)
        .code_programme_in(params.code_programme)
        .code_programme_not_in(params.not_code_programme)
        .annee_in(params.annee)
        .niveau_code_geo_in(params.niveau_geo, params.code_geo, source_region)
        .lieu_action_code_qpv_in(params.code_qpv, source_region)
        .centres_couts_in(params.centres_couts)
        .themes_in(params.theme)
        .beneficiaire_siret_in(params.beneficiaire_code)
        .categorie_juridique_in(
            params.beneficiaire_categorieJuridique_type,
            includes_none=params.beneficiaire_categorieJuridique_type is not None
            and "autres" in params.beneficiaire_categorieJuridique_type,
        )
        .source_region_in(_regions)
    )

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
    source_region = app_layer_sanitize_region(params.source_region, params.data_source)
    assert source_region is not None
    _regions = get_request_regions(source_region)

    # On requête toutes les colonnes
    params.colonnes = [c.code for c in get_list_colonnes_tableau()]
    params.colonnes.append("id")

    builder = (
        QpvQueryBuilder(db, params)
        .code_programme_in(params.code_programme)
        .code_programme_not_in(params.not_code_programme)
        .annee_in(params.annee)
        .niveau_code_geo_in(params.niveau_geo, params.code_geo, source_region)
        .lieu_action_code_qpv_in(params.code_qpv, source_region)
        .centres_couts_in(params.centres_couts)
        .themes_in(params.theme)
        .beneficiaire_siret_in(params.beneficiaire_code)
        .categorie_juridique_in(
            params.beneficiaire_categorieJuridique_type,
            includes_none=params.beneficiaire_categorieJuridique_type is not None
            and "autres" in params.beneficiaire_categorieJuridique_type,
        )
        .source_region_in(_regions)
        .sort_by_params()
    )

    if additionnal_source_region:
        _sanitized = app_layer_sanitize_region(additionnal_source_region)
        assert _sanitized is not None
        _regions.append(_sanitized)
        builder = builder.source_region_in([_sanitized], can_be_null=False)

    # Pagination et récupération des données
    builder = builder.paginate()
    data, has_next = builder.select_all()
    # TODO : Perfs
    total = builder.get_total("lignes")
    return [_to_enriched_ffl(x) for x in data], total, has_next


def get_annees_qpv(db: Session, params: SourcesQueryParams):
    params.source_region = app_layer_sanitize_region(params.source_region, params.data_source)
    assert params.source_region is not None
    _regions = get_request_regions(params.source_region)

    builder = (
        SourcesQueryBuilder(db, params)
        .select_custom_colonnes([distinct(EnrichedFlattenFinancialLinesDataQPV.annee).label("annee")])
        .source_region_in(_regions)
        .data_source_is(params.data_source)
    )
    data, has_next = builder.select_all()
    return [item["annee"] for item in data]


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
        _get_line_chart_annees(query_builder),
    )
    print(results)
    return DashboardData(
        total_financements=results[0]["total_financements"],
        total_actions=results[0]["total_actions"],
        total_porteurs=results[0]["total_porteurs"],
        pie_chart_themes=results[1],
        pie_chart_types_porteurs=results[2],
        line_chart_annees=results[3],
    )

async def _get_big_numbers(query_builder: QpvQueryBuilder):
    # Total des montants
    query_total_financements = query_builder.with_selection(select(func.coalesce(func.sum(EnrichedFlattenFinancialLinesDataQPV.montant_ae), 0.0)))
    total_financements = query_total_financements.select_one()
    # Nombres d'AE
    query_total_actions = query_builder.with_selection(select(func.coalesce(func.count(func.distinct(EnrichedFlattenFinancialLinesDataQPV.id)), 0.0)))
    total_actions = query_total_actions.select_one()
    # Nombre de bénéficiaires
    query_total_porteurs = query_builder.with_selection(select(func.coalesce(func.count(func.distinct(EnrichedFlattenFinancialLinesDataQPV.beneficiaire_code)), 0.0)))
    total_porteurs = query_total_porteurs.select_one()

    return {
        "total_financements": total_financements,
        "total_actions": total_actions,
        "total_porteurs": total_porteurs,
    }

async def _get_pie_chart_themes(query_builder: QpvQueryBuilder):
    qb = query_builder.with_selection([
        EnrichedFlattenFinancialLinesDataQPV.programme_theme.label("theme"),
        func.coalesce(func.sum(EnrichedFlattenFinancialLinesDataQPV.montant_ae), 0.0).label("total"),
    ])
    qb._query = qb._query.group_by(EnrichedFlattenFinancialLinesDataQPV.programme_theme)
    rows = qb._session.execute(qb._query).all()
    return ChartData(labels=[str(r.theme) for r in rows], values=[float(r.total or 0) for r in rows])


async def _get_pie_chart_types_porteur(query_builder: QpvQueryBuilder):
    qb = query_builder.with_selection([
        EnrichedFlattenFinancialLinesDataQPV.beneficiaire_categorieJuridique_type.label("type_porteur"),
        func.coalesce(func.sum(EnrichedFlattenFinancialLinesDataQPV.montant_ae), 0.0).label("total"),
    ])
    qb._query = qb._query.group_by(EnrichedFlattenFinancialLinesDataQPV.beneficiaire_categorieJuridique_type)
    rows = qb._session.execute(qb._query).all()
    return ChartData(labels=[str(r.type_porteur) for r in rows], values=[float(r.total or 0) for r in rows])


async def _get_line_chart_annees(query_builder: QpvQueryBuilder):
    qb = query_builder.with_selection([
        EnrichedFlattenFinancialLinesDataQPV.annee.label("annee"),
        func.coalesce(func.sum(EnrichedFlattenFinancialLinesDataQPV.montant_ae), 0.0).label("total"),
    ])
    qb._query = qb._query.group_by(EnrichedFlattenFinancialLinesDataQPV.annee)
    rows = qb._session.execute(qb._query).all()
    return ChartData(labels=[str(r.annee) for r in rows], values=[float(r.total or 0) for r in rows])