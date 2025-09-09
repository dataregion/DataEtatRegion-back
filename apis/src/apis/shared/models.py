from datetime import datetime
from http import HTTPStatus
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, computed_field, model_validator
from typing import Any, Generic, List, Literal, Optional, TypeVar, Union
from zoneinfo import ZoneInfo

_JSONSchemaType = Literal[
    "string", "number", "integer", "boolean", "object", "array", "null"
]
JSONSchemaType = Union[_JSONSchemaType, List[_JSONSchemaType]]


T = TypeVar("T")

_model_config: ConfigDict = {
    "json_encoders": {datetime: lambda dt: str(int(dt.timestamp()))}
}


def _ts_default_factory():
    dt = datetime.now(ZoneInfo("Europe/Paris"))
    dt = dt.replace(microsecond=0)
    return dt


class PaginationMeta(BaseModel):

    current_page: int
    has_next: bool


class APIResponse(BaseModel):
    code: int
    success: Optional[bool] = None
    timestamp: datetime = Field(default_factory=_ts_default_factory)
    message: Optional[str] = None

    model_config = _model_config

    def model_post_init(self, _: Any) -> None:
        if isinstance(self.code, HTTPStatus):
            self.code = self.code.value

    def to_json_response(self):
        json_content = self.model_dump(mode="json")
        return JSONResponse(status_code=self.code, content=json_content)


def _api_error_example():
    return {
        "code": 422,
        "success": False,
        "timestamp": datetime.now(ZoneInfo("Europe/Paris")),
        "message": "Erreur de validation",
        "detail": "",
    }


class APIError(APIResponse):
    detail: Optional[str] = None

    def model_post_init(self, ctx: Any) -> None:
        super().model_post_init(ctx)
        self.success = False

    @classmethod
    def example(cls):
        return _api_error_example()

    model_config = _model_config | {
        "json_schema_extra": {"example": _api_error_example()}
    }


class APISuccess(APIResponse, Generic[T]):
    data: Optional[T] = None
    message: Optional[str] = None
    current_page: Optional[int] = Field(default=None, exclude=True, frozen=True)
    has_next: Optional[bool] = Field(default=None, exclude=True, frozen=True)

    model_config = _model_config

    @computed_field
    @property
    def pagination(self) -> Optional[PaginationMeta]:
        pm = None
        if self.current_page is not None and self.has_next is not None:
            pm = PaginationMeta(current_page=self.current_page, has_next=self.has_next)
        return pm

    def model_post_init(self, ctx: Any) -> None:
        super().model_post_init(ctx)
        self.success = True

    @model_validator(mode="after")
    def check_pagination_is_consistent(self):
        a = self.current_page is not None
        b = self.has_next is not None
        valid = (a and b) or (not a and not b)
        if not valid:
            raise ValueError(
                "Les champs current_page et has_next doivent être renseignés"
            )
        return self
