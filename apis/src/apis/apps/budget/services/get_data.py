from models.entities.financial.query.FlattenFinancialLines import (
    EnrichedFlattenFinancialLines,
)

from services.shared.source_query_builder import SourcesQueryBuilder
from services.shared.source_query_params import SourcesQueryParams
from sqlalchemy import distinct
from sqlalchemy.orm import Session

from models.utils import convert_exception
from services.budget.query_params import BudgetQueryParams
from services.regions import get_request_regions, sanitize_source_region_for_bdd_request
from services.utilities.observability import (
    gauge_of_currently_executing,
    summary_of_time,
)

from apis.shared.exceptions import NoCurrentRegion

from .GetTotalOfLignes import GetTotalOfLignes


app_layer_sanitize_region = convert_exception(ValueError, NoCurrentRegion)(sanitize_source_region_for_bdd_request)


@gauge_of_currently_executing()
@summary_of_time()
def get_ligne(db: Session, params: SourcesQueryParams, id: int):
    """
    Recherche la ligne budgetaire selon son ID et sa source region
    """
    assert params.source is not None

    source_region = app_layer_sanitize_region(params.source_region, params.data_source)
    assert source_region is not None
    _regions = get_request_regions(source_region)

    builder = (
        SourcesQueryBuilder(EnrichedFlattenFinancialLines, db, params)
        .par_identifiant_technique(params.source_datatype, id)
        .data_source_is(params.data_source)
        .source_region_in(_regions)
    )
    return builder.select_one()


@gauge_of_currently_executing()
@summary_of_time()
def get_lignes(
    db: Session,
    params: BudgetQueryParams,
    additionnal_source_region: str | None = None,
    force_no_cache: bool = False,
):
    """
    Retourne les lignes (ou groupings) d'une requête
    """
    from services.budget.lignes_financieres.get_data import get_lignes as services_get_lignes

    data, has_next, grouped, builder = services_get_lignes(
        db=db,
        params=params,
        additionnal_source_region=additionnal_source_region,
        fn_app_layer_sanitize_region=app_layer_sanitize_region,
    )

    # TODO : Perfs
    # RGA: j'ai ajouté un cache applicatif sur certains totaux, à voir si c'est suffisant
    total_retriever = GetTotalOfLignes(builder, force_no_cache=force_no_cache)
    total = total_retriever.retrieve_total(params, additionnal_source_region)

    return data, total, grouped, has_next


def get_annees_budget(db: Session, params: SourcesQueryParams):
    params = params.with_update(
        update={"source_region": app_layer_sanitize_region(params.source_region, params.data_source)}
    )
    _regions = get_request_regions(params.source_region)

    builder = (
        SourcesQueryBuilder(EnrichedFlattenFinancialLines, db, params)
        .select_custom_model_properties([distinct(EnrichedFlattenFinancialLines.annee).label("annee")])
        .source_region_in(_regions)
        .data_source_is(params.data_source)
    )

    data, has_next = builder.select_all()
    return [item["annee"] for item in data]
