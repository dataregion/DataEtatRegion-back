from typing import Annotated
from pydantic import TypeAdapter, ValidationError
import pytest

from apis.services.model.pydantic_annotation import (
    PydanticFromMarshmallowSchemaAnnotationFactory,
)

from models.entities.financial.query import EnrichedFlattenFinancialLines
from models.schemas.financial import EnrichedFlattenFinancialLinesSchema

from apis.services.model.schema_adapter import SchemaAdapter

from apis.services.model.enriched_financial_lines_mappers import enriched_ffl_mappers

from models.schemas.common import DataTypeField

from ._utils_test_model import (
    _CustomSchema,
    _SecondCustomSchema,
    PydanticedCustom,
    PydanticedSecondCustom,
    prune_none_and_empty,
    custom_raises,  # noqa: F401
    pydanticed_custom_type_adapter,  # noqa: F401
)

############
# Test du schema adapter


def test_schema_adapter():
    adapter = SchemaAdapter(_CustomSchema)

    py_schema = adapter.pydantic_schema(cls=_CustomSchema)
    assert py_schema is not None

    assert len(_CustomSchema._declared_fields) == len(py_schema["fields"])  # type: ignore


#############
# Blackbox tests
@pytest.mark.parametrize(
    "input,validate_pydantic_ex,marsh_fields_with_validation_err",
    (
        ({"id": 3, "name": "hello", "nickname": "The Hellow"}, None, set()),
        ({"name": "hello", "nickname": "The Hellow"}, ValidationError, set(("id",))),
        ({"id": 3, "name": "hello"}, None, set()),
    ),
)
def test_pydanticed_validation(
    pydanticed_custom_type_adapter,  # noqa: F811
    input,
    validate_pydantic_ex,
    marsh_fields_with_validation_err,
):
    ## Test validating through marshmallow schema
    v = _CustomSchema().validate(input)
    assert set(v.keys()) == marsh_fields_with_validation_err

    ## Test validating through pydantic
    with custom_raises(validate_pydantic_ex):
        pydanticed_custom_type_adapter.validate_python(input)


@pytest.mark.parametrize(
    "input,json_schema",
    (
        (
            {"id": 3, "name": "hello"},
            {
                "id": {"title": "Id", "type": "integer"},
                "name": {"title": "Name", "type": "string"},
                "nickname": {
                    "anyOf": [{"type": "string"}, {"type": "null"}],
                    "default": None,
                    "title": "Nickname",
                },
            },
        ),
    ),
)
def test_pydanticed_json_schema(
    pydanticed_custom_type_adapter,  # noqa: F811
    input,
    json_schema,
):
    produced_schema = pydanticed_custom_type_adapter.json_schema()
    assert produced_schema["properties"] == json_schema


@pytest.mark.parametrize(
    "input,reserialized",
    (({"id": 3, "name": "hello"}, {"id": 3, "name": "hello"}),),
)
def test_pydanticed_reserialized(
    pydanticed_custom_type_adapter,  # noqa: F811
    input,
    reserialized,
):  # noqa: F811
    reser_produced = pydanticed_custom_type_adapter.dump_python(input)
    assert reser_produced == reserialized


#############
# internal tests
def test_pydanticed_factory():
    """Test de non reg qui s'assure que les variables de classe sont bien cloisonnées par type concret"""

    assert id(PydanticedCustom) != id(PydanticedSecondCustom)

    assert isinstance(PydanticedCustom._marshmallow_schema_cls(), _CustomSchema)
    assert isinstance(PydanticedSecondCustom._marshmallow_schema_cls(), _SecondCustomSchema)

    assert not isinstance(PydanticedCustom._marshmallow_schema_cls(), _SecondCustomSchema)
    assert not isinstance(PydanticedSecondCustom._marshmallow_schema_cls(), _CustomSchema)


##############
# Test with a more concrete case
EnrichedFlattenFinancialLinesModelAnnotation = PydanticFromMarshmallowSchemaAnnotationFactory[
    EnrichedFlattenFinancialLinesSchema
].create(EnrichedFlattenFinancialLinesSchema, custom_fields_mappers=enriched_ffl_mappers)
EnrichedFlattenFinancialLinesModel = Annotated[dict, EnrichedFlattenFinancialLinesModelAnnotation]


def test_model_flatten_financial_lines():
    ta = TypeAdapter(EnrichedFlattenFinancialLinesModel)

    data = EnrichedFlattenFinancialLines()
    data.id = 1337
    data.n_ej = "test"
    data.n_poste_ej = 0

    def _assert_validate(input):
        validated = ta.validate_python(data)
        instance = prune_none_and_empty(validated)
        assert instance == {
            "id": 1337,
            "n_ej": "test",
            "n_poste_ej": 0,
        }

    _assert_validate(data)  # XXX Accepte le model sqlalchemy
    _assert_validate(  # XXX Et aussi du contenu déjà serialisé
        {
            "id": 1337,
            "n_ej": "test",
            "n_poste_ej": 0,
        }
    )

    # Serialization
    _json = ta.dump_json(data)
    assert _json is not None

    _python = ta.dump_python(data)
    assert _python is not None


def test_jsonschema_flatten_financial_lines():
    ts = TypeAdapter(EnrichedFlattenFinancialLinesModel)

    json_schema = ts.json_schema()

    source_enum_values = json_schema["properties"]["source"]["anyOf"][0]["enum"]
    expected_values = DataTypeField._member_values()
    assert source_enum_values == expected_values

    tags_items = json_schema["properties"]["tags"]["anyOf"][0]["items"]

    assert "$ref" in tags_items, "Les tags sont une reference à un autre composant"
