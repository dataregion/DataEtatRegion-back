from datetime import datetime
from http import HTTPStatus
from typing import Generic, TypeVar
from zoneinfo import ZoneInfo

from fastapi import Response
from fastapi.responses import JSONResponse


T = TypeVar("T")


class PaginationMeta:

    def __init__(self, current_page: int, has_next: bool):
        self.current_page = current_page
        self.has_next = has_next

    def to_dict(self):
        return {"current_page": self.current_page, "has_next": self.has_next}


class APIResponse:

    def __init__(self, success: bool, code: HTTPStatus):
        self.code = code
        self.success = success
        self.timestamp = datetime.now(ZoneInfo("Europe/Paris"))

    def to_clean_dict(self):
        clean = {}
        for attr, value in self.__dict__.items():
            clean[attr] = value
        clean["timestamp"] = self.timestamp.isoformat()
        return clean

    def to_json_response(self) -> JSONResponse:
        if self.code == HTTPStatus.NO_CONTENT:
            return Response(status_code=HTTPStatus.NO_CONTENT.value)
        return JSONResponse(
            status_code=self.code.value,
            content=(
                self.to_clean_dict() if self.code != HTTPStatus.NO_CONTENT else None
            ),
        )


class APIError(APIResponse):

    def __init__(
        self, code: HTTPStatus, error: str | None = None, detail: str | None = None
    ):
        super().__init__(False, code)
        self.error = error
        self.detail = detail


class APISuccess(APIResponse, Generic[T]):

    def __init__(
        self,
        code: HTTPStatus,
        data: T | list[T] | None = None,
        message: str | None = None,
        has_next: bool | None = None,
        current_page: int | None = None,
    ):
        super().__init__(True, code)
        self.data = data
        self.message = message
        if current_page is not None and has_next is not None:
            self.pagination = PaginationMeta(
                current_page=current_page, has_next=has_next
            ).to_dict()
