from sqlalchemy.orm import Session

from services.budget.query_builder import BudgetQueryBuilder
from services.budget.colonnes import get_list_colonnes_tableau
from services.regions import get_request_regions, sanitize_source_region_for_bdd_request

from services.budget.query_params import BudgetQueryParams


def get_lignes(
    db: Session,
    params: BudgetQueryParams,
    additionnal_source_region: str | None = None,
    fn_app_layer_sanitize_region=None,
):
    """Retourne les lignes (ou groupings) d'une requête"""
    if fn_app_layer_sanitize_region is None:
        fn_app_layer_sanitize_region = sanitize_source_region_for_bdd_request

    source_region = fn_app_layer_sanitize_region(params.source_region, params.data_source)
    _regions = get_request_regions(source_region)

    # On requête toutes les colonnes
    params = params.with_update(update={"colonnes": ",".join([c.code for c in get_list_colonnes_tableau()])})
    assert "id" in params.colonnes

    builder = (
        BudgetQueryBuilder(db, params)
        .beneficiaire_siret_in(params.beneficiaire_code_list)
        .code_programme_in(params.code_programme_list)
        .themes_in(params.theme_list)
        .annee_in(params.annee_list)
        .niveau_code_geo_in(params.niveau_geo_enum, params.code_geo_list, source_region)
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
        _sanitized = fn_app_layer_sanitize_region(additionnal_source_region)
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

    grouped = builder.groupby_colonne is not None

    return (data, has_next, grouped, builder)
