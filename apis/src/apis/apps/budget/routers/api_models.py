from models.entities.financial.query import EnrichedFlattenFinancialLines
from models.schemas.financial import EnrichedFlattenFinancialLinesSchema
from apis.apps.budget.models.grouped_data import GroupedData
from apis.apps.budget.models.total import Total


from pydantic import BaseModel


from typing import Annotated, Literal

from apis.services.model.pydantic_annotation import make_pydantic_annotation_from_marshmallow_lignes

PydanticEnrichedFlattenFinancialLinesModel = make_pydantic_annotation_from_marshmallow_lignes(
    EnrichedFlattenFinancialLinesSchema, True
)

LigneFinanciere = Annotated[EnrichedFlattenFinancialLines, PydanticEnrichedFlattenFinancialLinesModel]


class LignesFinancieres(BaseModel):
    type: Literal["lignes_financieres"] = "lignes_financieres"
    total: Total
    lignes: list[LigneFinanciere]


class Groupings(BaseModel):
    type: Literal["groupings"] = "groupings"
    total: Total
    groupings: list[GroupedData]
