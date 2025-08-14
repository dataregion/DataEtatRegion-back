from http import HTTPStatus

from apis.exception_handlers import error_responses
from fastapi import APIRouter

from apis.shared.models import APISuccess


router = APIRouter()


@router.get(
    "",
    summary="Healthcheck",
    response_model=APISuccess,
    responses=error_responses(),
)
def healthcheck():
    return APISuccess(code=HTTPStatus.OK, message="Healthcheck OK", data=None)
