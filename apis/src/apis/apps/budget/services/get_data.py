from models.entities.financial.query.FlattenFinancialLines import (
    EnrichedFlattenFinancialLines,
)

from sqlalchemy import distinct
from sqlalchemy.orm import Session

from services.regions import get_request_regions, sanitize_source_region_for_bdd_request
from services.utilities.observability import (
    gauge_of_currently_executing,
    summary_of_time,
)
from models.utils import convert_exception

from apis.apps.budget.models.budget_query_params import (
    FinancialLineQueryParams,
    SourcesQueryParams,
)
from apis.apps.budget.services.get_colonnes import get_list_colonnes_tableau
from apis.apps.budget.services.query_builder import (
    FinancialLineQueryBuilder,
    SourcesQueryBuilder,
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
    source_region = app_layer_sanitize_region(params.source_region, params.data_source)

    assert source_region is not None
    assert params.source is not None

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
def get_lignes(
    db: Session,
    params: FinancialLineQueryParams,
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
        FinancialLineQueryBuilder(db, params)
        .beneficiaire_siret_in(params.beneficiaire_code)
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
        .categorie_juridique_in(
            params.beneficiaire_categorieJuridique_type,
            includes_none=params.beneficiaire_categorieJuridique_type is not None
            and "autres" in params.beneficiaire_categorieJuridique_type,
        )
        .sort_by_params()
        .tags_fullname_in(params.tags)
    )

    if additionnal_source_region:
        _sanitized = app_layer_sanitize_region(additionnal_source_region)
        assert _sanitized is not None
        _regions.append(_sanitized)
        builder = builder.source_region_in([_sanitized], can_be_null=False)

    # Ajout de conditions liées à la mécanique de grouping
    if builder.dynamic_conditions is not None:
        for col, value in builder.dynamic_conditions.items():
            attr = getattr(builder._model, col)
            builder.where_field_is(attr, value)

    # Group by si nécessaire
    if builder.groupby_colonne:
        groups = []
        groups.append(builder.groupby_colonne.code)
        if builder.groupby_colonne.concatenate is not None:
            groups.append(builder.groupby_colonne.concatenate)
        builder._query = builder._query.group_by(*groups)

    # Pagination et récupération des données
    builder = builder.paginate()
    data, has_next = builder.select_all()
    # TODO : Perfs
    total_retriever = GetTotalOfLignes(builder)
    total = total_retriever.retrieve_total(params, additionnal_source_region)
    grouped = builder.groupby_colonne is not None

    return data, total, grouped, has_next


def get_annees_budget(db: Session, params: SourcesQueryParams):
    params.source_region = app_layer_sanitize_region(params.source_region, params.data_source)
    assert params.source_region is not None
    _regions = get_request_regions(params.source_region)

    builder = (
        SourcesQueryBuilder(db, params)
        .select_custom_model_properties([distinct(EnrichedFlattenFinancialLines.annee).label("annee")])
        .source_region_in(_regions)
        .data_source_is(params.data_source)
    )
    data, has_next = builder.select_all()
    return [item["annee"] for item in data]
