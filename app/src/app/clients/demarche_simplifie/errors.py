class ApiDemarchesSimplifieesException(Exception):
    pass


class InvalidTokenError(ApiDemarchesSimplifieesException):
    pass


class UnauthorizedOnDemarche(ApiDemarchesSimplifieesException):
    pass


class DemarcheNotFound(ApiDemarchesSimplifieesException):
    pass
