from pydantic import BaseModel
from enum import Enum


class ColumnType(str, Enum):
    """Types de colonnes supportés."""

    TEXT = "text"
    NUMERIC = "numeric"
    DATE = "date"
    DATETIME = "datetime"
    BOOL = "bool"


class ColumnIn(BaseModel):
    """Informations nécessaires pour configurer une colonne dans Superset."""

    id: str
    type: ColumnType
    is_index: bool
