from pydantic import BaseModel


class PublishResponse(BaseModel):
    success: bool
    message: str
    table_id: str
    rows_imported: int = 0
