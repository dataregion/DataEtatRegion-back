from models.entities.financial.query.FlattenFinancialLines import EnrichedFlattenFinancialLines, FlattenFinancialLines
from models.value_objects.common import TypeCodeGeo
from fastapi import Request
from sqlalchemy import func, select
from apis.budget.dtos.colonne import Colonne
from apis.budget.dtos.budget_query_params import BudgetQueryParams
from sqlalchemy.orm import Session

from apis.budget.financial_data.builder_query import BuilderQueryFinancialLine
from services.regions import get_request_regions, sanitize_source_region_for_bdd_request
from services.utilities.observability import gauge_of_currently_executing, summary_of_time
from services.utils import convert_exception

from apis.utils.exceptions import NoCurrentRegion


def get_list_colonnes_tableau() -> list[Colonne]:
    return [
        Colonne(code=EnrichedFlattenFinancialLines.source.description, label="Source de données"),
        Colonne(code=EnrichedFlattenFinancialLines.n_ej.description, label="N° EJ"),
        Colonne(code=EnrichedFlattenFinancialLines.n_poste_ej.description, label="N° Poste EJ"),
        Colonne(code=EnrichedFlattenFinancialLines.montant_ae.description, label="Montant engagé"),
        Colonne(code=EnrichedFlattenFinancialLines.montant_cp.description, label="Montant payé"),
        Colonne(code=EnrichedFlattenFinancialLines.programme_theme.description, label="Thème"),
        Colonne(code=EnrichedFlattenFinancialLines.programme_code.description, label="Code programme"),
        Colonne(code=EnrichedFlattenFinancialLines.programme_label.description, label="Programme"),
        Colonne(code=EnrichedFlattenFinancialLines.domaineFonctionnel_code.description, label="Code domaine fonctionnel"),
        Colonne(code=EnrichedFlattenFinancialLines.domaineFonctionnel_label.description, label="Domaine fonctionnel"),
        Colonne(code=EnrichedFlattenFinancialLines.referentielProgrammation_label.description, label="Ref Programmation"),
        Colonne(code=EnrichedFlattenFinancialLines.beneficiaire_commune_label, label="Commune du SIRET"),
        Colonne(code=EnrichedFlattenFinancialLines.beneficiaire_commune_labelCrte.description, label="CRTE du SIRET"),
        Colonne(code=EnrichedFlattenFinancialLines.beneficiaire_commune_labelEpci.description, label="EPCI du SIRET"),
        Colonne(code=EnrichedFlattenFinancialLines.beneficiaire_commune_arrondissement_label.description, label="Arrondissement du SIRET"),
        Colonne(code=EnrichedFlattenFinancialLines.beneficiaire_commune_labelDepartement.description, label="Département du SIRET"),
        Colonne(code=EnrichedFlattenFinancialLines.beneficiaire_commune_labelRegion.description, label="Région du SIRET"),
        Colonne(code=EnrichedFlattenFinancialLines.localisationInterministerielle_code.description, label="Code localisation interministérielle"),
        Colonne(code=EnrichedFlattenFinancialLines.localisationInterministerielle_label.description, label="Localisation interministérielle"),
        Colonne(code=EnrichedFlattenFinancialLines.compte_budgetaire.description, label="Compte budgétaire"),
        Colonne(code=EnrichedFlattenFinancialLines.contrat_etat_region.description, label="CPER"),
        Colonne(code=EnrichedFlattenFinancialLines.groupeMarchandise_code.description, label="Code groupe marchandise"),
        Colonne(code=EnrichedFlattenFinancialLines.groupeMarchandise_label.description, label="Groupe marchandise"),
        Colonne(code=EnrichedFlattenFinancialLines.beneficiaire_code.description, label="SIRET"),
        Colonne(code=EnrichedFlattenFinancialLines.beneficiaire_denomination.description, label="Bénéficiaire"),
        Colonne(code=EnrichedFlattenFinancialLines.beneficiaire_categorieJuridique_type.description, label="Type d'établissement"),
        Colonne(code=EnrichedFlattenFinancialLines.beneficiaire_qpv_code.description, label="Code QPV"),
        Colonne(code=EnrichedFlattenFinancialLines.beneficiaire_qpv_label.description, label="QPV"),
        Colonne(code=EnrichedFlattenFinancialLines.dateDeDernierPaiement.description, label="Date dernier paiement"),
        Colonne(code=EnrichedFlattenFinancialLines.dateDeCreation.description, label="Date création EJ"),
        Colonne(code=EnrichedFlattenFinancialLines.annee.description, label="Année Exercice comptable", type=int),
        Colonne(code=EnrichedFlattenFinancialLines.centreCouts_code.description, label="Code centre coûts"),
        Colonne(code=EnrichedFlattenFinancialLines.centreCouts_label.description, label="Label centre coûts"),
        Colonne(code=EnrichedFlattenFinancialLines.centreCouts_description.description, label="Centre coûts"),
        Colonne(code=EnrichedFlattenFinancialLines.tags.key, label="Tags"),
        Colonne(code=EnrichedFlattenFinancialLines.data_source.description, label="Source Chorus"),
        Colonne(code=EnrichedFlattenFinancialLines.date_modification.description, label="Date modification EJ")
    ]


def get_list_colonnes_grouping() -> list[Colonne]:
    return [
        Colonne(code=EnrichedFlattenFinancialLines.annee.description, label="Année exercie comptable", type=int),
        Colonne(code=EnrichedFlattenFinancialLines.beneficiaire_commune_labelRegion.description, label="Région du SIRET"),
        Colonne(code=EnrichedFlattenFinancialLines.beneficiaire_commune_labelDepartement.description, label="Département du SIRET"),
        Colonne(code=EnrichedFlattenFinancialLines.beneficiaire_commune_labelCrte.description, label="CRTE du SIRET"),
        Colonne(code=EnrichedFlattenFinancialLines.beneficiaire_commune_labelEpci.description, label="EPCI du SIRET"),
        Colonne(code=EnrichedFlattenFinancialLines.beneficiaire_commune_labelRegion.description, label="Commune du SIRET"),
        Colonne(code=EnrichedFlattenFinancialLines.beneficiaire_qpv_label.description, label="Code QPV"),
        Colonne(code=EnrichedFlattenFinancialLines.localisationInterministerielle_label.description, label="Localisation interministérielle"),
        Colonne(code=EnrichedFlattenFinancialLines.programme_theme.description, label="Thème"),
        Colonne(code=EnrichedFlattenFinancialLines.programme_code.description, label="Programme"),
        Colonne(code=EnrichedFlattenFinancialLines.domaineFonctionnel_label.description, label="Domaine fonctionnel"),
        Colonne(code=EnrichedFlattenFinancialLines.referentielProgrammation_label.description, label="Ref Programmation"),
        Colonne(code=EnrichedFlattenFinancialLines.centreCouts_description.description, label="Centre coûts"),
        Colonne(code=EnrichedFlattenFinancialLines.beneficiaire_denomination.description, label="Bénéficiaire"),
        Colonne(code=EnrichedFlattenFinancialLines.beneficiaire_categorieJuridique_type.description, label="Type d'établissement"),
        Colonne(code=EnrichedFlattenFinancialLines.compte_budgetaire.description, label="Compte budgétaire"),
        Colonne(code=EnrichedFlattenFinancialLines.groupeMarchandise_label.description, label="Groupe marchandise"),
        Colonne(code=EnrichedFlattenFinancialLines.tags.key, label="Tags")
    ]


app_layer_sanitize_region = convert_exception(ValueError, NoCurrentRegion)(sanitize_source_region_for_bdd_request)

@gauge_of_currently_executing()
@summary_of_time()
def get_results(db: Session, params: BudgetQueryParams):

    source_region = app_layer_sanitize_region(params.source_region, params.data_source)
    _regions = get_request_regions(source_region)

    builder = (
        BuilderQueryFinancialLine(db, params)
        .beneficiaire_siret_in(params.siret_beneficiaire)
        .code_programme_in(params.code_programme)
        .themes_in(params.theme)
        .annee_in(params.annee)
        .centres_couts_in(params.centres_couts)
        .domaine_fonctionnel_in(params.domaine_fonctionnel)
        .referentiel_programmation_in(params.referentiel_programmation)
        .n_ej_in(params.n_ej)
        .source_is(params.source)
        .data_source_is(params.data_source)
        .source_region_in(_regions)
        .type_categorie_juridique_du_beneficiaire_in(params.types_beneficiaire, includes_none=params.types_beneficiaire is not None and "autres" in params.types_beneficiaire)
        .tags_fullname_in(params.tags)
    )

    if params.niveau_geo is not None and params.code_geo is not None:
        builder.where_geo(TypeCodeGeo[params.niveau_geo.upper()], params.code_geo, source_region)

    if params.ref_qpv is not None:
        if params.code_qpv is not None:
            builder.where_geo_loc_qpv(TypeCodeGeo.QPV if params.ref_qpv == 2015 else TypeCodeGeo.QPV24, params.code_qpv, source_region)
        else:
            builder.where_qpv_not_null(EnrichedFlattenFinancialLines.lieu_action_code_qpv)

    # DYNAMIC CONDITIONS
    if builder.dynamic_conditions is not None:
        for col, value in builder.dynamic_conditions.items():
            print(col)
            print(value)
            builder.add_dynamic_condition(col, value)

    # GROUP BY
    if builder.groupby_colonne:
        builder._stmt = builder._stmt.group_by(builder.groupby_colonne.code)
    
    # ORDER BY
    if params.sort_by:
        sortby_colonne = getattr(EnrichedFlattenFinancialLines, params.sort_by, None)
        if sortby_colonne is not None:
            if params.sort_order == "desc":
                builder._stmt = builder._stmt.order_by(sortby_colonne.desc())
            else:
                builder._stmt = builder._stmt.order_by(sortby_colonne.asc())

    # Pagination
    offset = (params.page - 1) * params.page_size
    builder._stmt = builder._stmt.offset(offset).limit(params.page_size + 1)

    # Retrieve data
    data = None
    if builder.groupby_colonne:
        data = list(db.execute(builder._stmt).unique().mappings().all())
    else:
        data = list(db.execute(builder._stmt).unique().scalars().all())
    print(data)

    # Has next ?
    count_plus_one = len(data)
    data = data[:params.page_size]

    return builder.message, data, builder.groupby_colonne is not None, params.page_size < count_plus_one


def get_annees_budget(source_region: str | None = None, data_source: str | None = None):
    source_region = app_layer_sanitize_region(source_region, data_source)
    _regions = get_request_regions(source_region)

    query_annees_budget = BuilderQueryFinancialLine().source_region_in(_regions)
    return query_annees_budget.do_select_annees()