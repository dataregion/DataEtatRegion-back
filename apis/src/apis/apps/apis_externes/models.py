from enum import Enum
from typing import Any, Iterable
from pydantic import BaseModel


class CodeErreur(str, Enum):
    CODE_UNKNOWN = "UNKNOWN"
    CODE_CALL_FAILED = "REMOTE_CALL_FAILED"
    CODE_LIMIT_HIT = "LIMIT_HIT"
    CODE_INVALID_TOKEN = "INVALID_TOKEN"
    CODE_UNAUTHORIZED_ON_DEMARCHE = "UNAUTHORIZED_ON_DEMARCHE"
    CODE_DEMARCHE_NOT_FOUND = "DEMARCHE_NOT_FOUND"


class ApiExterneError(BaseModel):
    code: CodeErreur
    """Code d'erreur"""
    message: str
    """Description rapide"""

    remote_errors: Iterable[Any]
    """Liste des messages d'erreurs distantes, si applicable"""

    def to_json_response(self, code_http: int = 500):
        from fastapi.responses import JSONResponse

        json_content = self.model_dump(mode="json")
        response = JSONResponse(status_code=code_http, content=json_content)
        return response
