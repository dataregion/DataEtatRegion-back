from pydantic import BaseModel


class ColumnIn(BaseModel):
    """Informations nécessaires pour configurer une colonne dans Superset."""

    id: str
    type: str
    is_index: bool
