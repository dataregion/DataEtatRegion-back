from typing import List

from models.value_objects.colonne_csv import ColonneCsv
from services.shared.schema_csv import SchemaCsv


class ImportQpvLieuActionSchema(SchemaCsv):
    colonnes: List[ColonneCsv] = [
        ColonneCsv(name="annee_exercice", dtype=int, required=True, example=2025),
        ColonneCsv(name="ref_action", dtype=str, required=True, example="P147-001"),
        ColonneCsv(name="ej", dtype=str, required=True, example="1234567890"),
        ColonneCsv(name="code_qpv", dtype=str, required=True, example="QP044004"),
        ColonneCsv(name="code_qpv24", dtype=str, required=True, example="QN04404M"),
        ColonneCsv(name="montant_ventillé", dtype=float, required=True, example=1000),
        ColonneCsv(name="libellé action", dtype=str, required=True, example="Mission humanitaire."),
        ColonneCsv(name="siret", dtype=str, required=True, example="78467169500087"),
    ]
