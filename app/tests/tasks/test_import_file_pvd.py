from unittest.mock import patch, MagicMock

import pytest

from models.entities.refs.Commune import Commune
from app.services.communes import select_commune
from app.tasks.refs.update_ref_communes import import_file_pvd
from tests import TESTS_PATH

_data = TESTS_PATH / "data"


@pytest.fixture(scope="function")
def add_commune_la_gacilly(database):
    commune = Commune(
        **{
            "code": "56061",
            "label_commune": "La Gacilly",
            "code_departement": "56",
            "is_pvd": False,
            "date_pvd": None,
        }
    )
    database.session.add(commune)
    database.session.commit()
    yield commune
    database.session.execute(database.delete(Commune))
    database.session.commit()


@patch("app.tasks.refs.update_ref_communes.subtask")
def test_import_file_pvd(mock_subtask: MagicMock, add_commune_la_gacilly):
    # DO
    with patch("shutil.move", return_value=None):  # ne pas supprimer le fichier de tests :)
        import_file_pvd(_data / "pvd.csv")

    commune = select_commune("56061")
    assert commune.is_pvd is True
    assert commune.date_pvd.strftime("%d/%m/%Y") == "09/07/2021"