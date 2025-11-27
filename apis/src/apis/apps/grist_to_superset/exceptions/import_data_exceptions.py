class ImportDataGristException(Exception):
    """Exception de base pour l'import des données venant du grist"""

    pass


class DataInsertException(ImportDataGristException):
    """Exception levée lors d'une erreur d'insertion des données importées"""

    def __init__(self) -> None:
        super().__init__("Erreur lors de la tentative d'insertion des données importées")
