from dataclasses import dataclass


@dataclass
class CallErrorDescription:
    code: str
    description: str | None


class ApiGristException(Exception):
    pass


class ApiGristError(ApiGristException):
    """Erreur survenue lors de l'appel à l'API"""

    def __init__(self, call_error_description: CallErrorDescription) -> None:
        self.call_error_description = call_error_description


class TokenNotFound(ApiGristException):
    """Erreur survenue lorsqu'un token ets introuvable"""

    def __init__(self, id) -> None:
        self.call_error_description = CallErrorDescription(
            "400",
            f"Une erreur s'est produit sur l'ajout d'une clé d'API à l'utilisateur {id}",
        )
