from typing import Any, Protocol
from marshmallow import fields
from marshmallow import Schema
from pydantic_core import core_schema
import logging


# Map Marshmallow fields to Python/Pydantic types
def _regular_field_pyschema(field: fields.Field):
    if isinstance(field, fields.Str):
        return core_schema.str_schema()
    if isinstance(field, fields.Int):
        return core_schema.int_schema()
    if isinstance(field, fields.Bool):
        return core_schema.bool_schema()
    if isinstance(field, fields.Float):
        return core_schema.float_schema()
    if isinstance(field, fields.DateTime):
        return core_schema.str_schema()
    if isinstance(field, fields.Date):
        return core_schema.str_schema()
    if isinstance(field, fields.UUID):
        return core_schema.str_schema()
    if isinstance(field, fields.List):
        return core_schema.list_schema()
    if isinstance(field, fields.Dict):
        return core_schema.dict_schema()
    if isinstance(field, fields.Raw):
        return core_schema.any_schema()
    else:
        return None


class FieldMapper(Protocol):
    """Mapper qui donne (ou non) une correspondance entre un field marshmallow et un schema pydantic"""

    def __call__(
        self, field_name: str, field: fields.Field, adapter: "SchemaAdapter"
    ) -> Any | None: ...


class SchemaAdapter:
    """Adapte un field marshmallow à l'api core_schema pydantic"""

    def __init__(self, schema_cls: type[Schema]) -> None:
        self._schema_cls = schema_cls
        self._custom_mappers = []

        self._logger = logging.getLogger(__name__)

    def add_custom_mapper(self, mapper: FieldMapper):
        self._custom_mappers.append(mapper)

    def make_pydantic_field_schema(self, field_name: str, field: fields.Field):
        schema = None

        for mapper in self._custom_mappers:
            if schema is not None:
                break
            schema = mapper(field_name, field, self)

        if schema is None:
            schema = _regular_field_pyschema(field)

        if schema is None:
            raise RuntimeError(f"Pas de correspondance pour le field {field}")

        #
        if not field.required:
            schema = core_schema.with_default_schema(
                schema=core_schema.nullable_schema(schema),
                default=None,
            )

        return schema

    def pydantic_schema(self, **kwargs):
        """
        donne le schema pydantic
        les kwargs sont utilisés pour surcharger le constructeur de schema
        """

        field_schemas = {}

        for field_name, field_obj in self._schema_cls._declared_fields.items():
            if not isinstance(field_obj, fields.Field):
                self._logger.debug(
                    f"Le champ {field_name} du schema {self._schema_cls.__name__} n'est pas un champ marshmallow. On ignore."
                )
                continue

            required = field_obj.required
            field_schemas[field_name] = core_schema.typed_dict_field(
                self.make_pydantic_field_schema(field_name, field_obj),
                required=required,
            )

        opts = {
            "cls": self.__class__,
            "fields": field_schemas,
        } | kwargs

        typed_dict_schema = core_schema.typed_dict_schema(**opts)

        return typed_dict_schema
