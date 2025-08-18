from contextlib import contextmanager
from typing import Sequence, Type, Annotated

from marshmallow import Schema, fields
from pydantic import BaseModel, TypeAdapter
import pytest

from apis.services.model.pydantic_annotation import PydanticFromMarshmallowSchemaAnnotationFactory


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


PydanticedCustom = PydanticFromMarshmallowSchemaAnnotationFactory[_CustomSchema].create(
    _CustomSchema
)
PydanticedSecondCustom = PydanticFromMarshmallowSchemaAnnotationFactory[
    _SecondCustomSchema
].create(_SecondCustomSchema)

PydanticedModel = Annotated[dict, PydanticedCustom]


@pytest.fixture()
def pydanticed_custom_type_adapter():
    """Le TypeAdapter du model Pydantic custom"""
    return TypeAdapter(PydanticedModel)


class AStubModel(BaseModel):
    id: int


def prune_none_and_empty(d: dict) -> dict:
    def passing(v):
        if isinstance(v, Sequence):
            return len(v) > 0
        else:
            return v is not None

    d = {k: v for k, v in d.items() if passing(v)}
    return d
