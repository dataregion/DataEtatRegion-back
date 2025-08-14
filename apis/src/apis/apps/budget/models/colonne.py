from pydantic import BaseModel

from apis.shared.models import JSONSchemaType


class Colonne(BaseModel):

    code: str | None = None
    label: str | None = None
    type: JSONSchemaType = "string"
    default: bool = True
