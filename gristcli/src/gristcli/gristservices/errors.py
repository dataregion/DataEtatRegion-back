from dataclasses import dataclass


@dataclass
class CallErrorDescription:
    code: str
    description: str | None


class ApiGristException(Exception):
    pass


class ApiGristError(ApiGristException):
    """Error occurred during the API call"""

    def __init__(self, call_error_description: CallErrorDescription) -> None:
        self.call_error_description = call_error_description


class TokenNotFound(ApiGristException):
    """Error occurred when a token is not found"""

    def __init__(self, id) -> None:
        self.call_error_description = CallErrorDescription(
            "400",
            f"An error occurred while adding an API key to user {id}",
        )
