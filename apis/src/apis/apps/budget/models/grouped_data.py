from typing import Optional
from pydantic import BaseModel


class GroupedData(BaseModel):

    colonne: str | int | float
    total: int
    total_montant_engage: Optional[float] = None
    total_montant_paye: Optional[float] = None
