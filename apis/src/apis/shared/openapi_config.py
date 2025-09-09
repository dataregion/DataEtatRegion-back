from datetime import datetime
from http import HTTPStatus
from typing import Any, Dict, Optional, TypeAlias, Union
from zoneinfo import ZoneInfo

from apis.shared.models import APIError, APISuccess

ResponsesType: TypeAlias = Optional[Dict[Union[int, str], Dict[str, Any]]]


def build_api_success_response(
    is_list: bool = False,
    message: str = "Opération réussie",
) -> ResponsesType:
    now = datetime.now(ZoneInfo("Europe/Paris")).isoformat()
    data_example = [] if is_list else {}
    response: ResponsesType = {
        200: {
            "model": APISuccess,
            "description": message,
            "content": {
                "application/json": {
                    "example": {
                        "code": HTTPStatus.OK,
                        "success": True,
                        "timestamp": now,
                        "message": message,
                        "data": data_example,
                    }
                }
            },
        },
        422: {"model": APIError},
    }

    if is_list:
        response[200]["content"]["application/json"]["example"]["pagination"] = {
            "current_page": 1,
            "has_next": False,
        }

    return response
