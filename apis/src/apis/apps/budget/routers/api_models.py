import datetime
from models.entities.financial.query import EnrichedFlattenFinancialLines
from models.schemas.financial import EnrichedFlattenFinancialLinesSchema
from models.value_objects.grouped_data import GroupedData
from models.value_objects.total import Total


from pydantic import BaseModel, ConfigDict


from typing import Annotated, Literal, Optional

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


class ExportFinancialTask(BaseModel):
    """DTO pour l'entité ExportFinancialTask."""

    model_config = ConfigDict(from_attributes=True)

    username: str
    prefect_run_id: str
    target_format: str

    status: str
    name: str

    started_at: Optional[datetime.datetime]
    completed_at: Optional[datetime.datetime]
