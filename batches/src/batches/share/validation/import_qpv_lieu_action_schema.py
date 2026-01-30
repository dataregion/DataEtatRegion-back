from batches.share.validation.generic_colonne_csv import GenericColonneCsv
from batches.share.validation.validation_schema_csv import ExpectedColonnes, ValidationSchemaCsv


class ImportQpvLieuActionSchema(ValidationSchemaCsv):
    colonnes: ExpectedColonnes = [
        GenericColonneCsv(name="annee_exercice", dtype=int, required=True, example=2025),
        GenericColonneCsv(name="ref_action", dtype=str, required=True, example="P147-001"),
        GenericColonneCsv(name="ej", dtype=str, required=True, example="1234567890"),
        GenericColonneCsv(name="code_qpv", dtype=str, required=True, example="QP044004"),
        GenericColonneCsv(name="code_qpv24", dtype=str, required=True, example="QN04404M"),
        GenericColonneCsv(name="montant_ventillé", dtype=float, required=True, example=1000),
        GenericColonneCsv(name="libellé action", dtype=str, required=True, example="Mission humanitaire."),
        GenericColonneCsv(name="siret", dtype=str, required=True, example="78467169500087"),
    ]
