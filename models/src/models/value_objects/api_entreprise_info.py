from typing import Optional
from pydantic import BaseModel


class ApiEntrepriseInfo(BaseModel):
    """Informations nécessaires pour configurer un client API entreprise."""
    url: str
    token: str
    context: str
    recipient: int
    """siren du client"""
    object: str
    timeout_seconds: Optional[int] = None
