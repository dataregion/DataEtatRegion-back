from pydantic import BaseModel, Field

Type = type


class Colonne(BaseModel):

    code: str | None = None
    label: str | None = None
    default: bool = True
    concatenate: str | None = None

    type: Type = Field(str, exclude=True)
    """XXX: Type du champ du modèle en bdd. Dédié un usage interne du backend"""


Colonnes = list[Colonne]
