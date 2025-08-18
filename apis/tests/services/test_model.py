import json
from contextlib import contextmanager
from typing import Type
from marshmallow import Schema, fields
from pydantic import BaseModel, ValidationError
import pytest

from apis.services.model import PydanticedMarshmallowSchemaFactory
from apis.shared.models import APISuccess

from models.entities.financial.query import EnrichedFlattenFinancialLines
from models.schemas.financial import EnrichedFlattenFinancialLinesSchema


@contextmanager
def _asserting_exception():
    """an empty context manager"""
    try:
        yield
    except Exception:
        raise


def custom_raises(type_ex: Type[Exception]):
    if type_ex is None:
        return _asserting_exception()

    return pytest.raises(type_ex)


class _CustomSchema(Schema):
    id = fields.Int(required=True)
    name = fields.Str(required=True)
    nickname = fields.Str(required=False)


class _SecondCustomSchema(Schema):
    id = fields.Int(required=True)


PydanticedCustom = PydanticedMarshmallowSchemaFactory[_CustomSchema].create(
    _CustomSchema
)
PydanticedSecondCustom = PydanticedMarshmallowSchemaFactory[_SecondCustomSchema].create(
    _SecondCustomSchema
)


class _WrapperModel(BaseModel):
    data: PydanticedCustom  # type: ignore


def test_pydanticed_factory():

    assert id(PydanticedCustom) != id(PydanticedSecondCustom)

    assert PydanticedCustom._marshmallow_schema_cls == _CustomSchema
    assert PydanticedSecondCustom._marshmallow_schema_cls == _SecondCustomSchema


@pytest.mark.parametrize(
    "input,validate_pydantic_ex,marsh_fields_with_validation_err",
    (
        ({"id": 3, "name": "hello", "nickname": "The Hellow"}, None, set()),
        ({"name": "hello", "nickname": "The Hellow"}, ValidationError, set(("id",))),
        ({"id": 3, "name": "hello"}, None, set()),
    ),
)
def test_pydanticed_validation(
    input, validate_pydantic_ex, marsh_fields_with_validation_err
):

    v = _CustomSchema().validate(input)
    assert set(v.keys()) == marsh_fields_with_validation_err

    with custom_raises(validate_pydantic_ex):
        _ = _WrapperModel(data=input)


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
def test_pydanticed_json_schema(input, json_schema):

    wrapped = _WrapperModel(data=input)
    produced_schema = wrapped.model_json_schema()
    assert produced_schema["properties"]["data"]["properties"] == json_schema


@pytest.mark.parametrize(
    "input,reserialized",
    (({"id": 3, "name": "hello"}, {"data": {"id": 3, "name": "hello"}}),),
)
def test_pydanticed_reserialized(input, reserialized):

    wrapped = _WrapperModel(data=input)

    reser_produced = wrapped.model_dump(mode="python")
    assert reser_produced == reserialized


##############
# Test with a more concrete case
EnrichedFlattenFinancialLinesModel = PydanticedMarshmallowSchemaFactory[
    EnrichedFlattenFinancialLinesSchema
].create(EnrichedFlattenFinancialLinesSchema)


def test_model_flatten_financial_lines():

    data = EnrichedFlattenFinancialLines()
    data.id = 1337
    data.n_ej = "test"
    data.n_poste_ej = 0
    serialized = EnrichedFlattenFinancialLinesModel._marshmallow_schema.dump(obj=data)

    response = APISuccess[EnrichedFlattenFinancialLinesModel](
        code=200, data=serialized  # type: ignore
    )
    m_json_schema = response.model_json_schema()
    with open("/tmp/jsonschema", "w+") as f:
        schema_str = json.dumps(m_json_schema)
        f.write(schema_str)
