from models.entities.financial.query.FlattenFinancialLines import EnrichedFlattenFinancialLines, FlattenFinancialLines
from models.value_objects.common import TypeCodeGeo
from requests import Session
from fastapi import Request
from fastapi_sqlalchemy import db
from sqlalchemy import func, select
from models.dtos.colonne import Colonne
from models.dtos.budget_query_params import BudgetQueryParams

from services.exceptions.authentication import NoCurrentRegion
from services.financial_data.builder_query import BuilderQueryFinancialLine
from services.regions import get_request_regions, sanitize_source_region_for_bdd_request
from services.utilities.observability import gauge_of_currently_executing, summary_of_time
from services.utils import convert_exception

def get_list_colonnes_tableau() -> list[Colonne]:
    return [
        Colonne(code="source", label="Source de données"),
        Colonne(code="n_ej", label="N° EJ"),
        Colonne(code="n_post_ej", label="N° Poste EJ"),
        Colonne(code="montant_ae", label="Montant engagé"),
        Colonne(code="montant_cp", label="Montant payé"),
        Colonne(code="theme", label="Thème"),
        Colonne(code="code_programme", label="Code programme"),
        Colonne(code="nom_programme", label="Programme"),
        Colonne(code="code_domaine", label="Code domaine fonctionnel"),
        Colonne(code="domaine", label="Domaine fonctionnel"),
        Colonne(code="ref_programmation", label="Ref Programmation"),
        Colonne(code="label_commune", label="Commune du SIRET"),
        Colonne(code="label_crte", label="CRTE du SIRET"),
        Colonne(code="label_epci", label="EPCI du SIRET"),
        Colonne(code="label_arrondissement", label="Arrondissement du SIRET"),
        Colonne(code="label_departement", label="Département du SIRET"),
        Colonne(code="label_region", label="Région du SIRET"),
        Colonne(code="code_localisation_interministerielle", label="Code localisation interministérielle"),
        Colonne(code="localisation_interministerielle", label="Localisation interministérielle"),
        Colonne(code="compte_budgetaire", label="Compte budgétaire"),
        Colonne(code="contrat_etat_region", label="CPER"),
        Colonne(code="code_groupe_marchandise", label="Code groupe marchandise"),
        Colonne(code="groupe_marchandise", label="Groupe marchandise"),
        Colonne(code="siret", label="SIRET"),
        Colonne(code="beneficiaire", label="Bénéficiaire"),
        Colonne(code="type_etablissement", label="Type d'établissement"),
        Colonne(code="code_qpv", label="Code QPV"),
        Colonne(code="qpv", label="QPV"),
        Colonne(code="date_cp", label="Date dernier paiement"),
        Colonne(code="date_replication", label="Date création EJ"),
        Colonne(code="annee", label="Année Exercice comptable"),
        Colonne(code="code_centre_couts", label="Code centre coûts"),
        Colonne(code="centre_couts_label", label="Label centre coûts"),
        Colonne(code="centre_couts", label="Centre coûts"),
        Colonne(code="tags", label="Tags"),
        Colonne(code="data_source", label="Source Chorus"),
        Colonne(code="date_modification", label="Date modification EJ")
    ]


def get_list_colonnes_grouping() -> list[Colonne]:
    return [
        Colonne(code="annee", label="Année exercie comptable"),
        Colonne(code="label_region", label="Région du SIRET"),
        Colonne(code="label_departement", label="Département du SIRET"),
        Colonne(code="label_crte", label="CRTE du SIRET"),
        Colonne(code="label_epci", label="EPCI du SIRET"),
        Colonne(code="label_commune", label="Commune du SIRET"),
        Colonne(code="code_qpv", label="Code QPV"),
        Colonne(code="localisation_interministerielle", label="Localisation interministérielle"),
        Colonne(code="theme", label="Thème"),
        Colonne(code="programme", label="Programme"),
        Colonne(code="domaine_fonctionnel", label="Domaine fonctionnel"),
        Colonne(code="ref_programmation", label="Ref Programmation"),
        Colonne(code="centre_couts", label="Centre coûts"),
        Colonne(code="beneficiaire", label="Bénéficiaire"),
        Colonne(code="type_etablissement", label="Type d'établissement"),
        Colonne(code="compte_budgetaire", label="Compte budgétaire"),
        Colonne(code="groupe_marchandise", label="Groupe marchandise"),
        Colonne(code="tags", label="Tags")
    ]



def get_query_params(request: Request) -> BudgetQueryParams:
    qp = request.query_params
    params = BudgetQueryParams()
    # Mapping conditions
    params.source = qp.get("source", None)
    params.n_ej = qp.get("n_ej").split(",") if qp.get("n_ej") else None
    params.code_programme = qp.get("code_programme").split(",") if qp.get("code_programme") else None
    params.niveau_geo = qp.get("niveau_geo", None)
    params.code_geo = qp.get("code_geo").split(",") if qp.get("code_geo") else None
    params.ref_qpv = int(qp.get("ref_qpv")) if qp.get("ref_qpv") else None
    params.code_qpv = qp.get("code_qpv").split(",") if qp.get("code_qpv") else None
    params.theme = qp.get("theme").split("|") if qp.get("theme") else None
    params.siret_beneficiaire = qp.get("siret_beneficiaire").split(",") if qp.get("siret_beneficiaire") else None
    params.types_beneficiaire = qp.get("types_beneficiaire").split(",") if qp.get("types_beneficiaire") else None
    params.annee = [int(a) for a in qp.get("annee").split(",") if a] if qp.get("annee") else None
    params.centres_couts = qp.get("centres_couts").split(",") if qp.get("centres_couts") else None
    params.domaine_fonctionnel = qp.get("domaine_fonctionnel").split(",") if qp.get("domaine_fonctionnel") else None
    params.referentiel_programmation = qp.get("referentiel_programmation").split(",") if qp.get("referentiel_programmation") else None
    params.tags = qp.get("tags").split(",") if qp.get("tags") else None
    
    # Mapping params
    params.colonnes = [c for c in get_list_colonnes_tableau() if c.code in qp.get("colonnes").split(",")] if qp.get("colonnes") else None
    params.grouping = [c for c in get_list_colonnes_grouping() if c.code in qp.get("grouping").split(",")] if qp.get("grouping") else None
    params.grouped = qp.get("grouped").split(",") if qp.get("grouped") else None

    # Validation
    if bool(params.niveau_geo) ^ bool(params.code_geo):
        raise ValueError("Les paramètres niveau_geo et code_geo doivent être fournis ensemble.")
    
    if bool(params.ref_qpv) ^ bool(params.code_qpv):
        raise ValueError("Les paramètres ref_qpv et code_qpv doivent être fournis ensemble.")

    return params


def _grouping_mechanisme(grouping: list[Colonne], grouped: list[str] | None):
    if grouped is None or len(grouped) == 0:
        return grouping[0], None
    return _grouping_mechanisme(grouping[1:], grouped[1:])


app_layer_sanitize_region = convert_exception(ValueError, NoCurrentRegion)(sanitize_source_region_for_bdd_request)

@gauge_of_currently_executing()
@summary_of_time()
def get_results(params: BudgetQueryParams):

    query = None
    dynamic_conditions = None
    message = "Liste des données financières"

    source_region = app_layer_sanitize_region(params.source_region, params.data_source)
    _regions = get_request_regions(source_region)

    builder = (
        BuilderQueryFinancialLine(db.session)
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

        .where_geo(TypeCodeGeo[params.niveau_geo.upper()], params.code_geo, source_region)
        .tags_fullname_in(params.tags)
    )
    if params.code_qpv is not None:
        builder.where_geo_loc_qpv(TypeCodeGeo.QPV if params.ref_qpv == 2015 else TypeCodeGeo.QPV24, params.code_qpv, source_region)
    else:
        builder.where_qpv_not_null(EnrichedFlattenFinancialLines.lieu_action_code_qpv)
    
    # Grouping mechanism
    if params.grouping is not None and (params.grouped is None or len(params.grouped) < len(params.grouping)):

        groupby_colonne, dynamic_conditions = _grouping_mechanisme(params.grouping, params.grouped)
        colonnes = [
            groupby_colonne,
            func.count(EnrichedFlattenFinancialLines.id).label("total"),
            func.sum(EnrichedFlattenFinancialLines.montant_ae).label("total_montant_engage"),
            func.sum(EnrichedFlattenFinancialLines.montant_cp).label("total_montant_paye"),
        ]
        builder._stmt = select(*colonnes).group_by(groupby_colonne)
        message = "Liste des montants agrégés"
    else:
        # No grouping: use fields param
        if params.colonnes is not None:
            selected_fields = [getattr(EnrichedFlattenFinancialLines.__dict__, f) for f in params.fields if hasattr(EnrichedFlattenFinancialLines.__dict__, f)]
            builder._stmt = select(*selected_fields)
        else:
            builder._stmt = select(EnrichedFlattenFinancialLines)
    
    # ORDER BY
    if params.sort_by:
        sortby_colonne = getattr(EnrichedFlattenFinancialLines, params.sort_by, None)
        if sortby_colonne is not None:
            if params.sort_order == "desc":
                query = query.order_by(sortby_colonne.desc())
            else:
                query = query.order_by(sortby_colonne.asc())

    # Pagination
    offset = (params.page - 1) * params.page_size
    query = query.offset(offset).limit(params.page_size + 1)

    # Retrieve data
    data = list(db.session.execute(builder._stmt).unique().scalars().all())

    # Has next ?
    count_plus_one = len(data)
    data = data[:params.page_size]

    return message, data, params.page_size < count_plus_one