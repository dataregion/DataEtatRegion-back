from pydantic import BaseModel
from typing import Optional
from enum import Enum


class ColumnType(str, Enum):
    """Types de colonnes supportés."""

    TEXT = "Text"
    NUMERIC = "Numeric"
    INT = "Int"
    DATE = "Date"
    DATETIME = "DateTime"
    BOOL = "Bool"
    ANY = "Any"
    CHOICE = "Choice"
    CHOICELIST = "ChoiceList"


class ColumnIn(BaseModel):
    """Informations nécessaires pour configurer une colonne dans Superset."""

    id: str
    type: ColumnType
    is_index: bool
    timezone: Optional[str] = None  # Timezone pour les colonnes DateTime (ex: "Europe/Madrid")
