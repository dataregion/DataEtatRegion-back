from pydantic import BaseModel


class Total(BaseModel):
    total: int = 0
    total_montant_engage: float = 0.0
    total_montant_paye: float = 0.0
