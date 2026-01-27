from typing import Any, Optional, Type
from pydantic import BaseModel, Field


class ColonneCsv(BaseModel):
    name: str = Field(..., description="Nom exact de la colonne CSV")
    dtype: Optional[Type] = Field(None, description="Type Python attendu (str, int, float, etc.)")
    required: bool = Field(True, description="Colonne obligatoire ou non")
    example: Optional[Any] = Field(None, description="Valeur exemple pour génération du CSV")
