from http import HTTPStatus

from fastapi import APIRouter

from apis.shared.decorators import handle_exceptions
from apis.shared.models import APISuccess


router = APIRouter()

@router.get("")
@handle_exceptions
def healthcheck():
    return APISuccess(
        status_code=HTTPStatus.OK,
        message="Healthcheck OK",
        data=None
    ).to_json_response()