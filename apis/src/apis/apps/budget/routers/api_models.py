from models.entities.financial.query import EnrichedFlattenFinancialLines
from models.schemas.financial import EnrichedFlattenFinancialLinesSchema
from apis.apps.budget.models.grouped_data import GroupedData
from apis.apps.budget.models.total import Total


from pydantic import BaseModel


from typing import Annotated, Literal

from apis.services.model.enriched_financial_lines_mappers import enriched_ffl_mappers, enriched_ffl_pre_validation_transformer
from apis.services.model.pydantic_annotation import PydanticFromMarshmallowSchemaAnnotationFactory

PydanticEnrichedFlattenFinancialLinesModel = PydanticFromMarshmallowSchemaAnnotationFactory[
    EnrichedFlattenFinancialLinesSchema
].create(
    EnrichedFlattenFinancialLinesSchema,
    custom_fields_mappers=enriched_ffl_mappers,
    pre_validation_transformer=enriched_ffl_pre_validation_transformer,
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

