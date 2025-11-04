from pydantic import BaseModel


class ApiDataSubventionInfo(BaseModel):
    """Informations nécessaires pour configurer un client API data subvention."""

    url: str
    token: str
