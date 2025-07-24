from models.entities.financial.query.FlattenFinancialLines import EnrichedFlattenFinancialLines
from models.value_objects.common import DataType, TypeCodeGeo

from sqlalchemy import distinct
from sqlalchemy.orm import Session

from services.regions import get_request_regions, sanitize_source_region_for_bdd_request
from services.utilities.observability import gauge_of_currently_executing, summary_of_time
from services.utils import convert_exception

from apis.apps.budget.models.budget_query_params import FinancialLineQueryParams, SourcesQueryParams
from apis.apps.budget.services.query_builder import FinancialLineQueryBuilder, SourcesQueryBuilder
from apis.shared.exceptions import NoCurrentRegion


app_layer_sanitize_region = convert_exception(ValueError, NoCurrentRegion)(sanitize_source_region_for_bdd_request)

def get_ligne(db: Session, params: SourcesQueryParams, id: int):
    """
    Recherche la ligne budgetaire selon son ID et sa source region
    """
    source_region = app_layer_sanitize_region(params.source_region, params.data_source)
    _regions = get_request_regions(source_region)

    builder = (
        SourcesQueryBuilder(db, params)
        .par_identifiant_technique(params.source, id)
        .data_source_is(params.data_source)
        .source_region_in(_regions)
    )
    return builder.select_one()

@gauge_of_currently_executing()
@summary_of_time()
def get_lignes(db: Session, params: FinancialLineQueryParams):
    """
    Recherche la ligne budgetaire selon son ID et sa source region
    """
    source_region = app_layer_sanitize_region(params.source_region, params.data_source)
    _regions = get_request_regions(source_region)

    builder = (
        FinancialLineQueryBuilder(db, params)
        .beneficiaire_siret_in(params.siret_beneficiaire)
        .code_programme_in(params.code_programme)
        .themes_in(params.theme)
        .annee_in(params.annee)
        .niveau_code_geo_in(params.niveau_geo, params.code_geo, source_region)
        .niveau_code_qpv_in(params.ref_qpv, params.code_qpv, source_region)
        .annee_in(params.annee)
        .centres_couts_in(params.centres_couts)
        .domaine_fonctionnel_in(params.domaine_fonctionnel)
        .referentiel_programmation_in(params.referentiel_programmation)
        .n_ej_in(params.n_ej)
        .source_is(params.source)
        .data_source_is(params.data_source)
        .source_region_in(_regions)
        .categorie_juridique_in(params.types_beneficiaire, includes_none=params.types_beneficiaire is not None and "autres" in params.types_beneficiaire)
        .tags_fullname_in(params.tags)
    )

    # DYNAMIC CONDITIONS
    if builder.dynamic_conditions is not None:
        for col, value in builder.dynamic_conditions.items():
            builder.where_field_is(getattr(builder._model, col), value)

    # GROUP BY
    if builder.groupby_colonne:
        builder._query = builder._query.group_by(builder.groupby_colonne.code)

    # Retrieve data
    data, has_next = builder.select_all()

    return data, builder.groupby_colonne is not None, has_next


def get_annees_budget(db: Session, params: SourcesQueryParams):
    params.source_region = app_layer_sanitize_region(params.source_region, params.data_source)
    _regions = get_request_regions(params.source_region)

    builder = (
        SourcesQueryBuilder(db, params)
        .select_custom_colonnes([
            distinct(EnrichedFlattenFinancialLines.annee).label("annee")
        ])
        .source_region_in(_regions)
        .data_source_is(params.data_source)
    )
    data, has_next = builder.select_all()
    return [item["annee"] for item in data]