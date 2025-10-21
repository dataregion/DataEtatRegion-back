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
            code=EnrichedFlattenFinancialLines.beneficiaire_denomination.description,
            label="Porteur de projet",
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.beneficiaire_commune_label.description,
            label="Commune du porteur",
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.beneficiaire_commune_labelDepartement.description,
            label="Département du porteur",
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.montant_ae.description,
            label="Montant (AE)",
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.annee.description,
            label="Année",
            type=int,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.centreCouts_label.description,
            label="Financeur",
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.programme_theme.description,
            label="Thèmatique associée",
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.programme_label.description,
            label="Programme (BOP)",
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.lieu_action_label_qpv.description,
            label="QPV du lieu de l'action",
        ),
    ]


def validation_colonnes(params: FinancialLineQueryParams):
    if params.colonnes is not None:
        params.map_colonnes_tableau(get_list_colonnes_tableau())

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
