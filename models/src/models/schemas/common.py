from marshmallow import fields
from models.value_objects.common import DataType


class DataTypeField(fields.Field):
    def _jsonschema_type_mapping(self):
        return {"type": "string", "enum": [member.value for member in DataType]}