from pydantic import BaseModel


class GroupedData(BaseModel):
    colonne: str = ""
    label: str | int | float | None
    value: str | int | float | None
    total: int
    total_montant_engage: float = 0.0
    total_montant_paye: float = 0.0
