class ApiDemarchesSimplifieesException(Exception):
    description: str | None
    pass


class InvalidTokenError(ApiDemarchesSimplifieesException):
    pass


class UnauthorizedOnDemarche(ApiDemarchesSimplifieesException):
    pass


class DemarcheNotFound(ApiDemarchesSimplifieesException):
    pass
