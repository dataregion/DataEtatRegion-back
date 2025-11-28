from http import HTTPStatus

from models.exceptions import BadRequestError


class InvalidTokenError(BadRequestError):
    """Exception en cas de token non présent"""

    def __init__(
        self,
        code: HTTPStatus = HTTPStatus.UNAUTHORIZED,
        api_message: str | None = None,
    ) -> None:
        super().__init__(code, api_message=api_message)


class NoCurrentRegion(InvalidTokenError):
    """Exception en cas de paramètre 'current_region' invalide"""

    def __init__(self) -> None:
        super().__init__(api_message="Region de l'utilisateur invalide.")
