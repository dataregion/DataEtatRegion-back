from http import HTTPStatus


class _APIException(Exception):
    def __init__(
        self,
        code: HTTPStatus = HTTPStatus.INTERNAL_SERVER_ERROR,
        api_message: str | None = None,
    ) -> None:
        super().__init__(api_message)
        self.code = code
        self.api_message = api_message


class ServerError(_APIException):
    """Exception qui représente une 500"""

    def __init__(
        self,
        code: HTTPStatus = HTTPStatus.INTERNAL_SERVER_ERROR,
        api_message: str | None = None,
    ) -> None:
        super().__init__(code, api_message)


class BadRequestError(_APIException):
    """Exception qui représente une 400"""

    def __init__(
        self,
        code: HTTPStatus = HTTPStatus.BAD_REQUEST,
        api_message: str | None = None,
    ) -> None:
        super().__init__(code, api_message)


############


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
