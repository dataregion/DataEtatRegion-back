import pytest
from werkzeug.datastructures import FileStorage

from app.exceptions.exceptions import InvalidFile, FileNotAllowedException
from models.entities.audit.AuditInsertFinancialTasks import AuditInsertFinancialTasks
from app.servicesapp.financial_data import import_financial_data, import_national_data
from tests import TESTS_PATH
from app import db


_chorus = TESTS_PATH / "data" / "chorus"
_chorus_errors = _chorus / "errors"


@pytest.fixture(scope="function", autouse=True)
def cleanup_after_tests():
    yield
    # Exécutez des actions nécessaires après tous les tests
    db.session.execute(db.delete(AuditInsertFinancialTasks))
    db.session.commit()


def test_import_file_not_allowed():
    # DO
    sample_pdf = _chorus_errors / "sample.pdf"
    with open(sample_pdf, "rb") as f:
        fs = FileStorage(f)
        with pytest.raises(FileNotAllowedException, match=r"n'a pas l'extension requise"):
            import_financial_data(fs, fs, "35", 2023)  # type: ignore


def test_import_file_ae_not_complete():
    missing_column_csv = _chorus_errors / "chorus_ae_missing_column.csv"
    with open(missing_column_csv, "rb") as f:
        fs = FileStorage(f)
        with pytest.raises(InvalidFile):
            import_financial_data(fs, fs, "35", 2023)  # type: ignore


def test_import_financial_data_ok(database, session):
    filename_ae = str(_chorus / "chorus_ae.csv")
    filename_cp = str(_chorus / "financial_cp.csv")

    with open(filename_ae, "rb") as f_ae, open(filename_cp, "rb") as f_cp:
        fs_ae = FileStorage(f_ae)
        fs_cp = FileStorage(f_cp)
        import_financial_data(fs_ae, fs_cp, "53", 2019)  # type: ignore

    # ASSERT
    r: AuditInsertFinancialTasks = session.execute(database.select(AuditInsertFinancialTasks)).scalar_one_or_none()
    assert r.fichier_ae is not None, "Le fichier AE doit être renseigné"
    assert r.fichier_cp is not None, "Le fichier CP doit être renseigné"
    _annee: int = r.annee  # type: ignore
    assert _annee == 2019, "L'année d'import est 2019"


def test_import_file_national_not_allowed():
    # DO
    sample_pdf = _chorus_errors / "sample.pdf"
    with open(sample_pdf, "rb") as f:
        fs = FileStorage(f)
        with pytest.raises(FileNotAllowedException, match=r"n'a pas l'extension requise"):
            import_national_data(fs, fs, 2023)  # type: ignore


def test_import_national_data_ok(database, session):
    filename_ae = str(_chorus / "chorus_ae.csv")
    filename_cp = str(_chorus / "financial_cp.csv")

    with open(filename_ae, "rb") as f_ae, open(filename_cp, "rb") as f_cp:
        fs_ae = FileStorage(f_ae)
        fs_cp = FileStorage(f_cp)
        import_national_data(fs_ae, fs_cp, 2024, username="test_username", client_id="client")  # type: ignore

    # ASSERT
    r: AuditInsertFinancialTasks = session.execute(database.select(AuditInsertFinancialTasks)).scalar_one_or_none()
    assert r.fichier_ae is not None, "Le fichier AE doit être renseigné"
    assert r.fichier_cp is not None, "Le fichier CP doit être renseigné"
    _annee: int = r.annee  # type: ignore
    assert r.source_region == "NATIONAL"
    assert _annee == 2024
