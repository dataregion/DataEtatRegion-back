class ImportDataGristException(Exception):
    """Exception de base pour l'import des données venant du grist"""

    pass


class DataInsertIndexException(ImportDataGristException):
    """Exception levée lors d'une erreur d'insertion des données importées"""

    def __init__(self, message) -> None:
        super().__init__(message)


class DataInsertException(ImportDataGristException):
    """Exception levée lors d'une erreur d'insertion des données importées"""

    def __init__(self) -> None:
        super().__init__("Erreur lors de la tentative d'insertion des données importées")


class UserNotFoundException(ImportDataGristException):
    """Exception levée quand l'utilisateur n'est pas présent dans superset"""

    def __init__(self) -> None:
        super().__init__("Erreur lors de la tentative de liens avec Superset. Utilisateur non trouvé")
