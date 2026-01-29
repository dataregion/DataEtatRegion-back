from unittest.mock import patch

from models.entities.financial.FinancialAe import FinancialAe

from psycopg import IntegrityError
import pytest
from sqlalchemy import select, delete
from batches.database import init_persistence_module
from batches.prefect.import_file_qpv_lieu_action import import_file_qpv_lieu_action
from tests import TESTS_PATH
from tests.conftest import add_references, delete_references, patch_session_scope

from models.entities.financial.QpvLieuAction import QpvLieuAction
from models.entities.refs import Qpv

_data = TESTS_PATH / "data" / "qpv_lieu_action"


@pytest.fixture(scope="function")
def add_qpv_1(session):
    qpv_1 = Qpv(**{"code": "QN04404M", "label": "QPV Test 1"})
    session.add(qpv_1)
    session.commit()
    yield qpv_1
    session.execute(delete(Qpv))
    session.commit()


def test_import_file_qpv_lieu_action(session, add_qpv_1, patch_session_scope):
    with patch("shutil.move", return_value=None):  # ne pas supprimer le fichier de tests :)
        import_file_qpv_lieu_action(str(_data / "file_comma.csv"))

    # ASSERT
    data = session.execute(select(QpvLieuAction)).all()
    assert len(data) == 3

    data: QpvLieuAction = session.execute(
        select(QpvLieuAction).where(QpvLieuAction.n_ej == "2104697991")
    ).scalar_one_or_none()
    assert data.id is not None
    assert data.code_qpv == "QN04404M"
    assert data.ratio_montant == 1000

    session.execute(delete(QpvLieuAction))
    session.commit()
