from http import HTTPStatus
from apis.apps.budget.models.budget_query_params import FinancialLineQueryParams
from apis.shared.exceptions import BadRequestError
from models.entities.financial.query.FlattenFinancialLines import (
    EnrichedFlattenFinancialLines,
)

from apis.apps.budget.models.colonne import Colonne


def get_list_colonnes_tableau() -> list[Colonne]:
    return [
        Colonne(
            code=EnrichedFlattenFinancialLines.source.description,
            label="Source de données",
            default=False,
        ),
        Colonne(code=EnrichedFlattenFinancialLines.n_ej.description, label="N° EJ"),
        Colonne(
            code=EnrichedFlattenFinancialLines.n_poste_ej.description,
            label="N° Poste EJ",
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.montant_ae.description,
            label="Montant engagé",
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.montant_cp.description,
            label="Montant payé",
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.programme_theme.description,
            label="Thème",
            default=False,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.programme_code.description,
            label="Code programme",
            concatenate=EnrichedFlattenFinancialLines.programme_label.description,
            default=False,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.programme_label.description,
            label="Programme",
            default=False,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.domaineFonctionnel_code.description,
            label="Code domaine fonctionnel",
            concatenate=EnrichedFlattenFinancialLines.domaineFonctionnel_label.description,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.domaineFonctionnel_label.description,
            label="Domaine fonctionnel",
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.referentielProgrammation_code.description,
            label="Code Ref Programmation",
            concatenate=EnrichedFlattenFinancialLines.referentielProgrammation_label.description,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.referentielProgrammation_label.description,
            label="Ref Programmation",
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.beneficiaire_commune_code.description,
            label="Code Commune du SIRET",
            concatenate=EnrichedFlattenFinancialLines.beneficiaire_commune_label.description,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.beneficiaire_commune_label.description,
            label="Commune du SIRET",
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.beneficiaire_commune_codeCrte.description,
            label="Code CRTE du SIRET",
            concatenate=EnrichedFlattenFinancialLines.beneficiaire_commune_labelCrte.description,
            default=False,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.beneficiaire_commune_labelCrte.description,
            label="CRTE du SIRET",
            default=False,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.beneficiaire_commune_codeEpci.description,
            label="Code EPCI du SIRET",
            concatenate=EnrichedFlattenFinancialLines.beneficiaire_commune_labelEpci.description,
            default=False,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.beneficiaire_commune_labelEpci.description,
            label="EPCI du SIRET",
            default=False,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.beneficiaire_commune_arrondissement_code.description,
            label="Code Arrondissement du SIRET",
            concatenate=EnrichedFlattenFinancialLines.beneficiaire_commune_arrondissement_label.description,
            default=False,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.beneficiaire_commune_arrondissement_label.description,
            label="Arrondissement du SIRET",
            default=False,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.beneficiaire_commune_codeDepartement.description,
            label="Code Département du SIRET",
            concatenate=EnrichedFlattenFinancialLines.beneficiaire_commune_labelDepartement.description,
            default=False,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.beneficiaire_commune_labelDepartement.description,
            label="Département du SIRET",
            default=False,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.beneficiaire_commune_codeRegion.description,
            label="Code Région du SIRET",
            concatenate=EnrichedFlattenFinancialLines.beneficiaire_commune_labelRegion.description,
            default=False,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.beneficiaire_commune_labelRegion.description,
            label="Région du SIRET",
            default=False,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.localisationInterministerielle_code.description,
            label="Code localisation interministérielle",
            concatenate=EnrichedFlattenFinancialLines.localisationInterministerielle_label.description,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.localisationInterministerielle_label.description,
            label="Localisation interministérielle",
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.compte_budgetaire.description,
            label="Compte budgétaire",
            default=False,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.contrat_etat_region.description,
            label="CPER",
            default=False,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.groupeMarchandise_code.description,
            label="Code groupe marchandise",
            concatenate=EnrichedFlattenFinancialLines.groupeMarchandise_label.description,
            default=False,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.groupeMarchandise_label.description,
            label="Groupe marchandise",
            default=False,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.beneficiaire_code.description,
            label="SIRET",
            concatenate=EnrichedFlattenFinancialLines.beneficiaire_denomination.description,
            default=False,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.beneficiaire_denomination.description,
            label="Bénéficiaire",
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.beneficiaire_categorieJuridique_type.description,
            label="Type d'établissement",
            default=False,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.beneficiaire_qpv_code.description,
            label="Code QPV",
            concatenate=EnrichedFlattenFinancialLines.beneficiaire_qpv_label.description,
            default=False,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.beneficiaire_qpv_label.description,
            label="QPV",
            default=False,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.dateDeDernierPaiement.description,
            label="Date dernier paiement",
            default=False,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.dateDeCreation.description,
            label="Date création EJ",
            default=False,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.annee.description,
            label="Année Exercice comptable",
            type=int,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.centreCouts_code.description,
            label="Code centre coûts",
            concatenate=EnrichedFlattenFinancialLines.centreCouts_label.description,
            default=False,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.centreCouts_label.description,
            label="Label centre coûts",
            default=False,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.centreCouts_description.description,
            label="Centre coûts",
            default=False,
        ),
        Colonne(code=EnrichedFlattenFinancialLines.tags.key, label="Tags", type=list),
        Colonne(
            code=EnrichedFlattenFinancialLines.source_region.description,
            label="Source Région",
            default=False,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.data_source.description,
            label="Source Chorus",
            default=False,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.date_modification.description,
            label="Date modification EJ",
            default=False,
        ),
    ]


def get_list_colonnes_grouping() -> list[Colonne]:
    return [
        Colonne(
            code=EnrichedFlattenFinancialLines.annee.description,
            label="Année exercie comptable",
            type=int,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.beneficiaire_commune_codeRegion.description,
            label="Code Région du SIRET",
            concatenate=EnrichedFlattenFinancialLines.beneficiaire_commune_labelRegion.description,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.beneficiaire_commune_codeDepartement.description,
            label="Code Département du SIRET",
            concatenate=EnrichedFlattenFinancialLines.beneficiaire_commune_labelDepartement.description,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.beneficiaire_commune_codeCrte.description,
            label="Code CRTE du SIRET",
            concatenate=EnrichedFlattenFinancialLines.beneficiaire_commune_labelCrte.description,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.beneficiaire_commune_codeEpci.description,
            label="Code EPCI du SIRET",
            concatenate=EnrichedFlattenFinancialLines.beneficiaire_commune_labelEpci.description,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.beneficiaire_commune_code.description,
            label="Code Commune du SIRET",
            concatenate=EnrichedFlattenFinancialLines.beneficiaire_commune_label.description,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.beneficiaire_qpv_code.description,
            label="Code QPV",
            concatenate=EnrichedFlattenFinancialLines.beneficiaire_qpv_label.description,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.localisationInterministerielle_code.description,
            label="Code Localisation interministérielle",
            concatenate=EnrichedFlattenFinancialLines.localisationInterministerielle_label.description,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.programme_theme.description,
            label="Thème",
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.programme_code.description,
            label="Programme",
            concatenate=EnrichedFlattenFinancialLines.programme_label.description,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.domaineFonctionnel_code.description,
            label="Domaine fonctionnel",
            concatenate=EnrichedFlattenFinancialLines.domaineFonctionnel_label.description,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.referentielProgrammation_code.description,
            label="Ref Programmation",
            concatenate=EnrichedFlattenFinancialLines.referentielProgrammation_label.description,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.centreCouts_code.description,
            label="Centre coûts",
            concatenate=EnrichedFlattenFinancialLines.centreCouts_label.description,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.beneficiaire_code.description,
            label="Bénéficiaire",
            concatenate=EnrichedFlattenFinancialLines.beneficiaire_denomination.description,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.beneficiaire_categorieJuridique_type.description,
            label="Type d'établissement",
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.compte_budgetaire.description,
            label="Compte budgétaire",
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.groupeMarchandise_code.description,
            label="Groupe marchandise",
            concatenate=EnrichedFlattenFinancialLines.groupeMarchandise_label.description,
        ),
        Colonne(code=EnrichedFlattenFinancialLines.tags.key, label="Tags", type=list),
    ]


def validation_colonnes(params: FinancialLineQueryParams):
    if params.colonnes is not None:
        params.map_colonnes_tableau(get_list_colonnes_tableau())
    if params.grouping is not None:
        params.map_colonnes_grouping(get_list_colonnes_grouping())
        # Check la validité de la paire grouping et grouped
        if params.grouped is None and len(params.grouping) > 1:
            raise BadRequestError(
                code=HTTPStatus.BAD_REQUEST,
                api_message="Mauvaise utilisation des paramètres de grouping",
            )
        if params.grouped is not None and len(params.grouping) not in (
            len(params.grouped) + 1,
            len(params.grouped),
        ):
            raise BadRequestError(
                code=HTTPStatus.BAD_REQUEST,
                api_message="Mauvaise utilisation des paramètres de grouping",
            )

    if params.sort_by is not None and params.sort_by not in [x.code for x in get_list_colonnes_tableau()]:
        raise BadRequestError(
            code=HTTPStatus.BAD_REQUEST,
            api_message=f"La colonne demandée '{params.sort_by}' n'existe pas pour le tableau.",
        )

    if params.fields_search is not None and not all(
        field in [x.code for x in get_list_colonnes_tableau()] for field in params.fields_search
    ):
        raise BadRequestError(
            code=HTTPStatus.BAD_REQUEST,
            api_message=f"Les colonnes demandées '{params.fields_search}' n'existe pas pour la recherche.",
        )
