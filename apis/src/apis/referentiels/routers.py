from http import HTTPStatus

from fastapi import APIRouter

from apis.utils.annotations import handle_exceptions
from apis.utils.models import APISuccess


router = APIRouter()

@router.get("/healthcheck")
@handle_exceptions
def ofe():
    return APISuccess(
        status_code=HTTPStatus.OK,
        message="Healthcheck OK",
        data=None
    ).to_json_response()