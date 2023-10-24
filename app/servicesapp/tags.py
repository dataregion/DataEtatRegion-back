import logging
import pandas as pd

from werkzeug.datastructures import FileStorage

from app.services.file_service import check_file_and_save
from app.tasks.tags.manuels import PUT_TAGS_CSV_HEADERS, put_tags_to_ae_from_user_export

logger = logging.getLogger(__name__)


class TagsServiceAppException(Exception):
    """Root exception of the tags services"""

    def __init__(self, *args: object) -> None:
        super().__init__(*args)
        self.message = "Erreur inconnue"


class InvalidRequest(TagsServiceAppException):
    """Pour les 400"""

    pass


class InvalidFile(InvalidRequest):
    """Fichier invalide"""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message or "Erreur inconnue"

    pass


class InvalidHeadersInFile(InvalidFile):
    """Header non présent"""

    def __init__(self, headers_to_find: list[str]) -> None:
        _headers_pretty = " ou ".join(headers_to_find)
        _message = f"Le fichier ne contient pas de colonne {_headers_pretty}."
        super().__init__(_message)


class TagsAppService:
    def maj_ae_tags_from_export(self, file: FileStorage | None):
        if file is None:
            raise TagsServiceAppException("Aucun fichier n'est founi pour mettre à jour les tags !")

        input_file = check_file_and_save(file, in_unique_folder=True)

        _check_csv_has_necessary_headers(input_file)

        put_tags_to_ae_from_user_export.delay(input_file)


def _check_csv_has_necessary_headers(input_file: str):
    """Check the input file has necessary headers"""
    file_header = pd.read_csv(input_file, nrows=1)
    columns = file_header.columns
    for header_synonyms in PUT_TAGS_CSV_HEADERS:
        _in_columns = [x in columns for x in header_synonyms]
        _synonym_in_columns = any(_in_columns)
        if not _synonym_in_columns:
            raise InvalidHeadersInFile(header_synonyms)
