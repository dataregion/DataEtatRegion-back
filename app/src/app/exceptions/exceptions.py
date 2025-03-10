class DataRegatException(Exception):
    pass


class FinancialException(Exception):
    """
    Exception basique sur les Données financières
    """

    pass


class FinancialLineConcurrencyError(FinancialException):
    """Exception levée lorsque une insertion de ligne chorus échoue à cause de problème de concourrance."""

    pass


class BadRequestDataRegateNum(DataRegatException):
    def __init__(self, message=""):
        self.message = message
        super().__init__(f"Bad Request : {self.message}")


class FileNotAllowedException(DataRegatException):
    """Exception raised when file not allowed."""

    def __init__(self, name="FileNotAllowed", message="le fichier n'a pas la bonne extension"):
        self.message = message
        self.name = name
        super().__init__(f"[{self.name}] {self.message}")


class InvalidFile(DataRegatException):
    """Exception raised when file content is not correct."""

    def __init__(self, name="InvalidFile", message="le fichier contient des informations erronés"):
        self.message = message
        self.name = name
        super().__init__(f"[{self.name}] {self.message}")


class ConfigurationException(DataRegatException):
    """Exception raised when configuration is missing.

    Attributes:
        configuration_key (str): The configuration key
    """

    def __init__(self, configuration_key: str):
        self.message = f"Configuration for {configuration_key} missing"
        super().__init__(self.message)


class ValidTokenException(DataRegatException):
    """Exception raised when token is not valid"""

    def __init__(self):
        super().__init__("Forbidden")
