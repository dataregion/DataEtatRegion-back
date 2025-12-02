class ApiSupersetException(Exception):
    pass


class ApiSupersetError(ApiSupersetException):
    """Error occurred during the API call"""

    def __init__(self, description: str) -> None:
        self.description = description


class UserNotFound(ApiSupersetException):
    """Error occurred when a user is not found on superset"""

    def __init__(self) -> None:
        self.description = "Utilisateur introuvable sur Superset"
