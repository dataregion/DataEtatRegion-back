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


class InvalidGristDocIdException(ImportDataGristException):
    """Exception levée quand l'identifiant du document Grist est absent ou mal formé"""

    def __init__(self) -> None:
        super().__init__(
            "L'identifiant du document Grist est invalide. Rechargez le document dans Grist puis réessayez."
        )


class InvalidTableIdException(ImportDataGristException):
    """Exception levée quand l'identifiant de la table Grist contient des caractères non autorisés"""

    def __init__(self, table_id: str) -> None:
        super().__init__(f"L'identifiant de table « {table_id} » n'est pas valide.")


class PublishedTableNameTooLongException(ImportDataGristException):
    """Exception levée quand le nom de la table publiée dépasse la limite des identifiants PostgreSQL"""

    def __init__(self, table_id: str, max_table_id_length: int) -> None:
        super().__init__(
            f"Le nom de la table « {table_id} » est trop long pour être publié depuis ce document "
            f"({max_table_id_length} caractères au plus). Renommez la table pour la publier."
        )
