from pydantic import BaseModel


class Colonne(BaseModel):

    code: str | None = None
    label: str | None = None
    type: str | None = None
    default: bool = True
