from models.entities.financial.query.FlattenFinancialLines import (
    EnrichedFlattenFinancialLines,
)

from services.shared.source_query_builder import SourcesQueryBuilder
from services.shared.source_query_params import SourcesQueryParams
from sqlalchemy import distinct
from sqlalchemy.orm import Session

from models.utils import convert_exception
from services.budget.query_params import BudgetQueryParams
from services.budget.query_builder import BudgetQueryBuilder
from services.regions import get_request_regions, sanitize_source_region_for_bdd_request
from services.utilities.observability import (
    gauge_of_currently_executing,
    summary_of_time,
)

from apis.shared.exceptions import NoCurrentRegion
from services.budget.colonnes import get_list_colonnes_tableau

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
    Recherche la ligne budgetaire selon son ID et sa source region
    """
    source_region = app_layer_sanitize_region(params.source_region, params.data_source)
    assert source_region is not None
    _regions = get_request_regions(source_region)

    # On requête toutes les colonnes
    params = params.model_copy(update={"colonnes": ",".join([c.code for c in get_list_colonnes_tableau()])})
    assert "id" in params.colonnes

    builder = (
        BudgetQueryBuilder(db, params)
        .beneficiaire_siret_in(params.beneficiaire_code_list)
        .code_programme_in(params.code_programme_list)
        .themes_in(params.theme_list)
        .annee_in(params.annee_list)
        .niveau_code_geo_in(params.niveau_geo, params.code_geo_list, source_region)
        .centres_couts_in(params.centres_couts_list)
        .domaine_fonctionnel_in(params.domaine_fonctionnel_list)
        .referentiel_programmation_in(params.referentiel_programmation_list)
        .n_ej_in(params.n_ej_list)
        .source_is(params.source)
        .data_source_is(params.data_source)
        .source_region_in(_regions)
        .categorie_juridique_in(
            params.beneficiaire_categorieJuridique_type_list,
            includes_none=params.beneficiaire_categorieJuridique_type_list is not None
            and "autres" in params.beneficiaire_categorieJuridique_type_list,
        )
        .sort_by_params()
        .tags_fullname_in(params.tags_list)
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
    # RGA: j'ai ajouté un cache applicatif sur certains totaux, à voir si c'est suffisant
    total_retriever = GetTotalOfLignes(builder, force_no_cache=force_no_cache)
    total = total_retriever.retrieve_total(params, additionnal_source_region)
    grouped = builder.groupby_colonne is not None

    return data, total, grouped, has_next


def get_annees_budget(db: Session, params: SourcesQueryParams):
    params = params.model_copy(
        update={"source_region": app_layer_sanitize_region(params.source_region, params.data_source)}
    )
    assert params.source_region is not None
    _regions = get_request_regions(params.source_region)

    builder = (
        SourcesQueryBuilder(EnrichedFlattenFinancialLines, db, params)
        .select_custom_model_properties([distinct(EnrichedFlattenFinancialLines.annee).label("annee")])
        .source_region_in(_regions)
        .data_source_is(params.data_source)
    )

    data, has_next = builder.select_all()
    return [item["annee"] for item in data]
