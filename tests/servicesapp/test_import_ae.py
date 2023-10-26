import re

import pytest
from werkzeug.datastructures import FileStorage

from app.exceptions.exceptions import InvalidFile, FileNotAllowedException
from app.servicesapp.financial_data import import_ae
from tests import DATA_PATH

_chorus_errors = DATA_PATH / "data" / "chorus" / "errors"


def test_import_import_file_ae_file_not_allowed():
    # DO
    sample_pdf = _chorus_errors / "sample.pdf"
    with open(sample_pdf, "rb") as f:
        with pytest.raises(FileNotAllowedException, match=r"n'a pas l'extension requise"):
            import_ae(FileStorage(f), "35", 2023, False)

    sample_csv = _chorus_errors / "sample.csv"
    with open(sample_csv, "rb") as f:
        with pytest.raises(FileNotAllowedException, match=re.escape("[FileNotAllowed] Erreur de lecture du fichier")):
            import_ae(FileStorage(f), "35", 2023, False)


def test_import_file_ae_not_complete():
    missing_column_csv = _chorus_errors / "chorue_ae_missing_column.csv"
    with open(missing_column_csv, "rb") as f:
        with pytest.raises(InvalidFile):
            import_ae(FileStorage(f), "35", 2023, False)
