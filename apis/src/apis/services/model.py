from marshmallow import Schema
from marshmallow import fields
from pydantic_core import SchemaValidator, core_schema
from typing import Any, Generic, Type, TypeVar


T = TypeVar("T", bound=Schema)

# Map Marshmallow fields to Python/Pydantic types
SCHEMAS_MAPPING = {
    fields.Str: core_schema.str_schema(),
    fields.Int: core_schema.int_schema(),
    fields.Bool: core_schema.bool_schema(),
    fields.Float: core_schema.float_schema(),
    fields.DateTime: core_schema.str_schema(),
    fields.Date: core_schema.str_schema(),
    fields.UUID: core_schema.str_schema(),
    fields.List: core_schema.list_schema(),
    fields.Dict: core_schema.dict_schema(),
    fields.Raw: core_schema.any_schema(),
}


def get_pydantic_schema(field_obj):
    field_type = type(field_obj)
    py_schema = SCHEMAS_MAPPING.get(field_type, core_schema.any_schema())
    if not field_obj.required:
        py_schema = core_schema.with_default_schema(
            core_schema.nullable_schema(py_schema),
            default=None,
        )
    return py_schema


def from_marshmallow_schema(schema_cls):
    mfs: dict[str, Any] = {}
    mfs = {}

    for field_name, field_obj in schema_cls._declared_fields.items():
        mfs[field_name] = core_schema.model_field(
            schema=get_pydantic_schema(field_obj),
        )

    return core_schema.model_fields_schema(mfs)


class PydanticedMarshmallowSchemaFactory(Generic[T]):
    def __init__(self) -> None:
        super().__init__()

    @classmethod
    def create(cls, marshmallow_schema_cls: Type[T]):
        _class = PydanticedMarshmallowSchema[T]
        _class.set_marsh_schema(marshmallow_schema_cls)
        return _class


class PydanticedMarshmallowSchema(Generic[T]):

    def __init__(self) -> None:
        super().__init__()

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler):

        cls._schema = from_marshmallow_schema(cls._marshmallow_schema_cls)

        fn = core_schema.no_info_plain_validator_function(
            function=cls._validate,
            json_schema_input_schema=cls._schema,
        )
        return fn

    @classmethod
    def _validate(cls, input_val):
        v = SchemaValidator(cls._schema)
        v.validate_python(input_val)
        return input_val

    @classmethod
    def set_marsh_schema(cls, marshmallow_schema: Type[T]):
        cls._marshmallow_schema_cls = marshmallow_schema
        cls._marshmallow_schema = cls._marshmallow_schema_cls()

    def __class_getitem__(cls, item):
        # Return a new subclass for each concrete type
        name = f"{cls.__name__}[{item.__name__}]"
        t = type(name, (cls,), {"__type_param__": item})
        return t
