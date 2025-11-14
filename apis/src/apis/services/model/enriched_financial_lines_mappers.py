"""
Module des field mappers custom pour l'objet EnrichedFlattenFinancialLines
"""

from pydantic_core import core_schema
from apis.services.model.schema_adapter import SchemaAdapter

from models.value_objects.common import DataType
from models.schemas.common import DataTypeField


def enriched_ffl_tags_mapper(field_name, field, adapter):
    if field_name != "tags":
        return None

    _model_cls = type("Tags", (dict,), dict(dict.__dict__))

    tag_marshmallow_schema_cls = field.inner.nested
    _tag_adapter = SchemaAdapter(tag_marshmallow_schema_cls)
    items_schema = _tag_adapter.pydantic_schema(cls=_model_cls, ref="Tags")
    list_schema = core_schema.list_schema(items_schema=items_schema)
    return list_schema


def enriched_ffl_data_type_mapper(field_name, field, adapter):
    if isinstance(field, DataTypeField):
        return core_schema.enum_schema(DataType, list(DataType.__members__.values()))
    return None


ffl_mappers = [enriched_ffl_data_type_mapper]


def enriched_ffl_pre_validation_transformer(input_value):
    if "source" in input_value is not None:
        input_value["source"] = DataType(input_value["source"])
    return input_value


def get_mappers(enriched: bool = False):
    return ffl_mappers if not enriched else ffl_mappers + [enriched_ffl_tags_mapper]
