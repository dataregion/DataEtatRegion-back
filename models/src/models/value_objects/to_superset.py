from pydantic import BaseModel
from enum import Enum


class ColumnType(str, Enum):
    """Types de colonnes supportés."""

    TEXT = "Text"
    NUMERIC = "Numeric"
    INT = "Int"
    DATE = "Date"
    DATETIME = "Datetime"
    BOOL = "Bool"
    ANY = "Any"
    CHOICE = "Choice"
    CHOICELIST = "ChoiceList"

class ColumnIn(BaseModel):
    """Informations nécessaires pour configurer une colonne dans Superset."""

    id: str
    type: ColumnType
    is_index: bool
