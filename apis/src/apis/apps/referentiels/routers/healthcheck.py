from http import HTTPStatus

from apis.shared.openapi_config import build_api_success_response
from fastapi import APIRouter

from apis.shared.decorators import handle_exceptions
from apis.shared.models import APISuccess
from fastapi.responses import JSONResponse


router = APIRouter()


@router.get(
    "",
    summary="Healthcheck",
    response_class=JSONResponse,
    responses=build_api_success_response(),
)
@handle_exceptions
def healthcheck():
    return APISuccess(status_code=HTTPStatus.OK, message="Healthcheck OK", data=None)
