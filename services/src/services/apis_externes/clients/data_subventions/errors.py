from dataclasses import dataclass


@dataclass
class CallErrorDescription:
    status_code: str
    """Status code de l'appel HTTP distant"""
    api_code: str | None
    """Code API de l'erreur"""
    message: str | None
    """Message de l'erreur"""


class ApiDataSubventionException(Exception):
    pass


class CallError(ApiDataSubventionException):
    """Erreur survenue lors de l'appel à l'API"""

    def __init__(self, call_error_description: CallErrorDescription) -> None:
        self.call_error_description = call_error_description
