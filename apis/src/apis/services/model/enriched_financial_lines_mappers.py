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

    class _ModelClass(dict):
        model_config = {"title": "Tags"}

    tag_marshmallow_schema_cls = field.inner.nested
    _tag_adapter = SchemaAdapter(tag_marshmallow_schema_cls)
    items_schema = _tag_adapter.pydantic_schema(cls=_ModelClass, ref="Tags")
    list_schema = core_schema.list_schema(items_schema=items_schema)
    return list_schema

def enriched_ffl_data_type_mapper(field_name, field, adapter):
    if isinstance(field, DataTypeField):
        return core_schema.enum_schema(
            DataType, list(DataType.__members__.values())
        )
    return None

enriched_ffl_mappers = [
    enriched_ffl_data_type_mapper,
    enriched_ffl_tags_mapper,
]