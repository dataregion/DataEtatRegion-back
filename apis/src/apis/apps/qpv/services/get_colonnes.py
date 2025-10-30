from http import HTTPStatus
from apis.apps.qpv.models.qpv_query_params import QpvQueryParams
from apis.shared.exceptions import BadRequestError
from models.entities.financial.query.FlattenFinancialLinesDataQpv import (
    FlattenFinancialLinesDataQPV,
)

from apis.apps.budget.models.colonne import Colonne


def get_list_colonnes_tableau() -> list[Colonne]:
    return [
        Colonne(
            code=FlattenFinancialLinesDataQPV.beneficiaire_code.description,
            label="Code du porteur de projet",
        ),
        Colonne(
            code=FlattenFinancialLinesDataQPV.beneficiaire_denomination.description,
            label="Porteur de projet",
        ),
        Colonne(
            code=FlattenFinancialLinesDataQPV.beneficiaire_commune_code.description,
            label="Code commune du porteur",
        ),
        Colonne(
            code=FlattenFinancialLinesDataQPV.beneficiaire_commune_label.description,
            label="Commune du porteur",
        ),
        Colonne(
            code=FlattenFinancialLinesDataQPV.beneficiaire_commune_codeDepartement.description,
            label="Code département du porteur",
        ),
        Colonne(
            code=FlattenFinancialLinesDataQPV.beneficiaire_commune_labelDepartement.description,
            label="Département du porteur",
        ),
        Colonne(
            code=FlattenFinancialLinesDataQPV.montant_ae.description,
            label="Montant (AE)",
        ),
        Colonne(
            code=FlattenFinancialLinesDataQPV.annee.description,
            label="Année",
            type=int,
        ),
        Colonne(
            code=FlattenFinancialLinesDataQPV.centreCouts_code.description,
            label="Code financeur",
        ),
        Colonne(
            code=FlattenFinancialLinesDataQPV.centreCouts_label.description,
            label="Financeur",
        ),
        Colonne(
            code=FlattenFinancialLinesDataQPV.programme_code.description,
            label="Code programme (BOP)",
        ),
        Colonne(
            code=FlattenFinancialLinesDataQPV.programme_label.description,
            label="Programme (BOP)",
        ),
        Colonne(
            code=FlattenFinancialLinesDataQPV.programme_theme.description,
            label="Thèmatique associée",
        ),
        Colonne(
            code=FlattenFinancialLinesDataQPV.lieu_action_code_qpv.description,
            label="Code QPV du lieu de l'action",
        ),
        Colonne(
            code=FlattenFinancialLinesDataQPV.lieu_action_label_qpv.description,
            label="QPV du lieu de l'action",
        ),
    ]


def validation_colonnes(params: QpvQueryParams):
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
