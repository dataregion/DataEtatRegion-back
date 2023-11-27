from enum import Enum
from marshmallow import fields


class DataType(Enum):
    FINANCIAL_DATA_AE = "FINANCIAL_DATA_AE"
    FINANCIAL_DATA_CP = "FINANCIAL_DATA_CP"
    FRANCE_RELANCE = "FRANCE_RELANCE"
    FRANCE_2030 = "FRANCE_2030"
    ADEME = "ADEME"
    REFERENTIEL = "REFERENTIEL"


class DataTypeField(fields.Field):
    def _jsonschema_type_mapping(self):
        return {"type": "string", "enum": [member.value for member in DataType]}
