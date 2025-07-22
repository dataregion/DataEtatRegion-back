
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from http import HTTPStatus
from typing import Generic, Literal, TypeVar

from fastapi import Query, Request
from fastapi.responses import JSONResponse


T = TypeVar("T")

@dataclass
class PaginationMeta:
  current_page: int
  has_next: bool


@dataclass
class APIResponse:
  code: HTTPStatus
  success: bool | None = None
  timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

  def to_clean_dict(self):
    clean = {}
    for attr, value in self.__dict__.items():
        if attr != "code":
          clean[attr] = value
    clean["timestamp"] = self.timestamp.isoformat()
    return clean
  
  def to_json_response(self) -> JSONResponse:
    return JSONResponse(
        status_code=self.code.value,
        content=self.to_clean_dict()
    )


@dataclass
class APIError(APIResponse):
  error: str | None = None
  detail: str | None = None

  def __post_init__(self):
    self.success = False


@dataclass
class APISuccess(APIResponse, Generic[T]):
  data: T | list[T] | None = None
  message: str | None = None
  pagination: PaginationMeta | None = None

  def __post_init__(self):
    self.success = True
    if not isinstance(self.data, list):
      self.pagination = None

  def set_pagination(self, current_page: int, has_next: bool):
    if isinstance(self.data, list):
      self.pagination = PaginationMeta(current_page=current_page, has_next=has_next)


