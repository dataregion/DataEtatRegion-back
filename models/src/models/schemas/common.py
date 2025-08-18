from marshmallow import fields
from models.value_objects.common import DataType


class DataTypeField(fields.Field):
    
    @classmethod
    def _member_values(cls):
        return [member.value for member in DataType]

    def _jsonschema_type_mapping(self):
        return {"type": "string", "enum": self.__class__._member_values()}
