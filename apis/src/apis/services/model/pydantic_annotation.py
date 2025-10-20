import logging
from marshmallow import Schema, post_dump
from pydantic_core import SchemaValidator, core_schema
from apis.services.model.schema_adapter import FieldMapper, SchemaAdapter
from models.schemas.utils import MarshmallowSafeGetAttrMixin


from typing import Any, Generic, Type, TypeVar
from marshmallow import fields

###
TSchema = TypeVar("TSchema", bound=Schema)


##
def _pydantic_python_dump_marshmallow_schema(schema_cls: type[Schema]):
    """
    Fabrique un schema marshmallow spécialisé
    avec des comportements supplémentaires spécifique à la logique d'adaptation marshamallow / pydantic
    """

    class _PydanticPythonDumpMarshmallowSchema(schema_cls):
        def _serialize(self, obj: Any, *, many: bool = False):
            return super()._serialize(obj, many=many)

        @post_dump(pass_original=True)
        def post_dump(self, data, original, many, **kwargs):
            if not hasattr(original, "__dict__"):
                return data

            # XXX On garde les valeurs originales pour les DateTime
            # puisque pydantic garde les objet datetime lors de la serialisation en python
            for field_name, field_obj in self.fields.items():
                if isinstance(field_obj, fields.DateTime) and field_name in data:
                    original_value = self.get_attribute(original, field_name, None)
                    if original_value is not None:
                        data[field_name] = original_value

            return data

    return _PydanticPythonDumpMarshmallowSchema


class PydanticFromMarshmallowSchemaAnnotation(Generic[TSchema]):
    """Annotation qui ajoute les routines pydantic à partir d'un schema marshmallow"""

    def __init__(self) -> None:
        super().__init__()

    @classmethod
    def from_marshmallow_schema(cls, schema_cls):
        sa = SchemaAdapter(schema_cls)

        for mapper in cls._custom_field_mapper:
            sa.add_custom_mapper(mapper)

        pydantic_schema = sa.pydantic_schema(cls=cls._model_cls)
        return pydantic_schema

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler):
        cls._schema = cls.from_marshmallow_schema(cls._marshmallow_schema_cls)

        serialization = core_schema.wrap_serializer_function_ser_schema(
            function=cls._serialize,
            return_schema=cls._schema,
        )
        fn = core_schema.no_info_wrap_validator_function(
            serialization=serialization,
            function=cls._validate,
            schema=cls._schema,
            ref=cls._model_cls.__name__,
        )
        return fn

    @classmethod
    def __get_pydantic_json_schema__(cls, core_schema, handler):
        json_schema = handler(cls._schema)
        json_schema = handler.resolve_ref_schema(json_schema)
        return json_schema

    @classmethod
    def pre_validation_transform(cls, input_value):
        if cls._custom_pre_validation_transformer is not None:
            return cls._custom_pre_validation_transformer(input_value)
        return input_value

    @classmethod
    def _validate(cls, input_val, _):
        marshmallow_model_cls = cls._get_inner_marshmallow_model_or_none()
        if marshmallow_model_cls is not None and isinstance(input_val, marshmallow_model_cls):
            input_val = cls._marshmallow_schema.dump(input_val)

        input_val = cls.pre_validation_transform(input_val)
        v = SchemaValidator(cls._schema)
        v.validate_python(input_val, strict=False)
        return input_val

    @classmethod
    def _serialize(cls, obj, handler):
        marshmallow_model_cls = cls._get_inner_marshmallow_model_or_none()
        if marshmallow_model_cls is not None and isinstance(obj, marshmallow_model_cls):
            obj = cls._marshmallow_schema.dump(obj)
        return obj

    @classmethod
    def _get_inner_marshmallow_model_or_none(cls):
        try:
            marshmallow_model_cls = cls._marshmallow_schema_cls.Meta.model
            return marshmallow_model_cls
        except Exception:
            cls._logger.debug(
                "Impossible de déterminer le modèle marshmallow `Schema.Meta.model`. It could be a good idea to add one."
            )
        return None

    @classmethod
    def _init_class(
        cls,
        marshmallow_schema: Type[TSchema],
        custom_field_mappers: list[FieldMapper] | None = None,
        pre_validation_transformer=None,
    ):
        #
        # Initialize avec le marshmallow schema
        #
        cls._marshmallow_schema_cls = _pydantic_python_dump_marshmallow_schema(marshmallow_schema)
        cls._marshmallow_schema = cls._marshmallow_schema_cls()
        cls._logger = logging.getLogger(f"{cls.__name__}[{cls._marshmallow_schema_cls.__name__}]")
        if isinstance(cls._marshmallow_schema, MarshmallowSafeGetAttrMixin):
            cls._logger.info(
                f"Activation du mode safe_getattr pour {cls._marshmallow_schema_cls.__name__}. Les erreurs d'accès au modèle seront ignorées."
            )
            cls._marshmallow_schema.enable_safe_getattr()

        #
        _cls_to_use = cls._get_inner_marshmallow_model_or_none()
        if _cls_to_use is None:
            _cls_to_use = cls._marshmallow_schema_cls

        #
        cls._model_cls = type(_cls_to_use.__name__, (dict,), dict(dict.__dict__))

        #
        cls._custom_field_mapper = []
        if custom_field_mappers is not None:
            cls._custom_field_mapper = custom_field_mappers

        cls._custom_pre_validation_transformer = None
        if pre_validation_transformer is not None:
            cls._custom_pre_validation_transformer = pre_validation_transformer

    def __class_getitem__(cls, item):
        # Return a new subclass for each concrete type
        name = f"{cls.__name__}[{item.__name__}]"
        t = type(name, (cls,), {"__type_param__": item})
        return t


class PydanticFromMarshmallowSchemaAnnotationFactory(Generic[TSchema]):
    def __init__(self) -> None:
        super().__init__()

    @classmethod
    def create(
        cls,
        marshmallow_schema_cls: Type[TSchema],
        custom_fields_mappers: list[FieldMapper] | None = None,
        pre_validation_transformer=None,
    ):
        if custom_fields_mappers is None:
            custom_fields_mappers = []
        _class = PydanticFromMarshmallowSchemaAnnotation[TSchema]
        _class._init_class(
            marshmallow_schema_cls,
            custom_field_mappers=custom_fields_mappers,
            pre_validation_transformer=pre_validation_transformer,
        )
        return _class
