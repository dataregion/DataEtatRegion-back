from models.entities.financial.query.FlattenFinancialLinesDataQpv import (
    FlattenFinancialLinesDataQPV,
)

from models.value_objects.colonne import Colonne


def get_list_colonnes_tableau() -> list[Colonne]:
    return [
        Colonne(
            code=FlattenFinancialLinesDataQPV.id.description,
            label="ID",
        ),
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
