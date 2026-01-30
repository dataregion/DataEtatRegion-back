from unittest.mock import patch

import pytest
from sqlalchemy import select, delete
from batches.prefect.import_file_qpv_lieu_action import import_file_qpv_lieu_action
from tests import TESTS_PATH
from tests.conftest import patch_session_scope  # noqa: F401

from models.entities.financial.QpvLieuAction import QpvLieuAction
from models.entities.refs import Qpv

_data = TESTS_PATH / "data" / "qpv_lieu_action"


@pytest.fixture(scope="function")
def add_qpv(session, patch_session_scope):  # noqa: F811
    """
    Fixture d'ajout de QPV obligatoire
    Il y a une foreign_key sur la table QpvLieuAction
    """
    qpv_1 = Qpv(**{"code": "QN04404M", "label": "QPV Test"})
    session.add(qpv_1)
    session.commit()
    yield qpv_1
    session.execute(delete(Qpv))
    session.commit()


def test_import_file_qpv_lieu_action(session, add_qpv, patch_session_scope):  # noqa: F811
    """
    Dans ce test le fichier est parfaitement valide
    On s'attend à ce que les trois lignes soient insérées
    """

    # On ne touche pas au fichier de tests, on ne créé pas de sauvegarde
    with (
        patch("shutil.move", return_value=None),
        patch("shutil.copy", return_value=None),
        patch("os.makedirs", return_value=None),
    ):
        import_file_qpv_lieu_action.fn(str(_data / "file_comma.csv"))

    # ASSERT
    data = session.execute(select(QpvLieuAction)).all()
    assert len(data) == 3

    data: QpvLieuAction = session.execute(
        select(QpvLieuAction).where(QpvLieuAction.ej == "2104697991")
    ).scalar_one_or_none()
    assert data.id is not None
    assert data.code_qpv == "QN04404M"
    assert data.montant_ventille == 1000

    session.execute(delete(QpvLieuAction))
    session.commit()


def test_import_file_qpv_lieu_action_missing_col(session, add_qpv, patch_session_scope):  # noqa: F811
    """
    Dans ce test, il manque une colonne dans le fichier
    On s'attend à une exception, c'est une règle de validation hard
    """

    # Structure non conforme, exception levée
    with pytest.raises(ValueError):
        import_file_qpv_lieu_action.fn(str(_data / "file_comma_missing_col.csv"))

    # ASSERT
    data = session.execute(select(QpvLieuAction)).all()
    assert len(data) == 0


def test_import_file_qpv_lieu_action_missing_data(session, add_qpv, patch_session_scope):  # noqa: F811
    """
    Dans ce test, il manque la valeur de l'année pour deux lignes
    On s'attend à ce que ces deux lignes soient ignorées, c'est une validation soft
    """

    # On ne touche pas au fichier de tests, on ne créé pas de sauvegarde
    with (
        patch("shutil.move", return_value=None),
        patch("shutil.copy", return_value=None),
        patch("os.makedirs", return_value=None),
    ):
        import_file_qpv_lieu_action.fn(str(_data / "file_comma_missing_data.csv"))

    # ASSERT
    data = session.execute(select(QpvLieuAction)).all()
    assert len(data) == 1

    session.execute(delete(QpvLieuAction))
    session.commit()


def test_import_file_qpv_lieu_action_wrong_type(session, add_qpv, patch_session_scope):  # noqa: F811
    """
    Dans ce test, la valeur de l'année est mal typée pour deux lignes
    On s'attend à ce que ces deux lignes soient ignorées, c'est une validation soft
    """

    # On ne touche pas au fichier de tests, on ne créé pas de sauvegarde
    with (
        patch("shutil.move", return_value=None),
        patch("shutil.copy", return_value=None),
        patch("os.makedirs", return_value=None),
    ):
        import_file_qpv_lieu_action.fn(str(_data / "file_comma_wrong_type.csv"))

    # ASSERT
    data = session.execute(select(QpvLieuAction)).all()
    assert len(data) == 0

    session.execute(delete(QpvLieuAction))
    session.commit()
