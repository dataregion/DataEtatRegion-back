from datetime import datetime
from http import HTTPStatus
from pydantic import BaseModel, Field, model_validator
from typing import Generic, Optional, TypeVar
from zoneinfo import ZoneInfo


T = TypeVar("T")


class PaginationMeta(BaseModel):

    def __init__(self, current_page: int, has_next: bool):
        self.current_page = current_page
        self.has_next = has_next

    def to_dict(self):
        return {"current_page": self.current_page, "has_next": self.has_next}


class APIResponse(BaseModel):
    code: int
    success: bool
    timestamp: datetime = Field(
        default_factory=lambda _: datetime.now(ZoneInfo("Europe/Paris"))
    )
    message: Optional[str] = None

    def __init__(self, **data):
        code = data.get("code")
        if "success" not in data:
            data["success"] = True
        if isinstance(code, HTTPStatus):
            data["code"] = code.value
        super().__init__(**data)


class APIError(APIResponse):
    detail: Optional[str] = None

    def __init__(self, **data):
        super().__init__(**data)
        data["success"] = False

    class Config:
        json_schema_extra = {
            "example": {
                "code": 422,
                "success": False,
                "timestamp": datetime.now(ZoneInfo("Europe/Paris")),
                "message": "Erreur de validation",
                "detail": "",
            }
        }


class APISuccess(APIResponse, Generic[T]):
    data: Optional[T] = None
    message: Optional[str] = None
    current_page: Optional[int] = Field(default=None, exclude=True)
    has_next: Optional[bool] = Field(default=None, exclude=True)

    @model_validator(mode="before")
    @classmethod
    def build_pagination(cls, values):
        current_page = values.get("current_page")
        has_next = values.get("has_next")
        if current_page is not None and has_next is not None:
            values["pagination"] = PaginationMeta(
                current_page=current_page, has_next=has_next
            )
        return values
