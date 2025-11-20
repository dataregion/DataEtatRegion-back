from pydantic import BaseModel


class ColumnIn(BaseModel):
    id: str
    type: str
    is_index: bool
