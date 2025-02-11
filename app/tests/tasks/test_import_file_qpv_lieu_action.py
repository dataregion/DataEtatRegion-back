from datetime import date
from unittest.mock import patch, call, ANY, MagicMock

from models.entities.financial.QpvLieuAction import QpvLieuAction
from app.tasks.financial.import_financial import import_file_qpv_lieu_action
from models.entities.refs import Qpv
from psycopg import IntegrityError
import pytest
from tests import TESTS_PATH
from tests import delete_references

_data = TESTS_PATH / "data"

@pytest.fixture(scope="function")
def add_qpv_1(database):
    qpv_1 = Qpv(
        **{
            "code": "QP044017",
            "label": "QPV Test 1"
        }
    )
    database.session.add(qpv_1)
    database.session.commit()
    yield qpv_1
    database.session.execute(database.delete(Qpv))
    database.session.commit()

@pytest.fixture(scope="function")
def add_qpv_2(database):
    qpv_2 = Qpv(
        **{
            "code": "QP044011",
            "label": "QPV Test 2"
        }
    )
    database.session.add(qpv_2)
    database.session.commit()
    yield qpv_2
    database.session.execute(database.delete(Qpv))
    database.session.commit()


def test_import_file_qpv_lieu_action(app, database, session, add_qpv_1, add_qpv_2):
    # DO
    with patch("shutil.move", return_value=None):  # ne pas supprimer le fichier de tests :)
        import_file_qpv_lieu_action(_data / "qpv_lieu_action.csv")

    # ASSERT
    data = session.execute(database.select(QpvLieuAction)).all()
    assert len(data) == 2

    data: QpvLieuAction = session.execute(database.select(QpvLieuAction).where(QpvLieuAction.n_ej == "2103609602")).scalar_one_or_none()
    assert data.id is not None
    assert data.code_qpv == "QP044017"
    assert data.ratio_montant == 5000
    delete_references(session)
