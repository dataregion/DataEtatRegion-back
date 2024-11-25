from unittest.mock import patch, MagicMock

import pytest

from models.entities.refs.Commune import Commune
from models.entities.refs.LocalisationInterministerielle import LocalisationInterministerielle
from app.services.communes import select_commune
from app.tasks.refs.update_ref_communes import import_file_acv
from tests import TESTS_PATH

_data = TESTS_PATH / "data"


@pytest.fixture(scope="function")
def add_commune_la_gacilly(database):
    commune = Commune(
        **{
            "code": "35288",
            "label_commune": "Saint-Malo",
            "code_departement": "35",
            "is_acv": False,
            "date_acv": None,
        }
    )
    database.session.add(commune)
    database.session.commit()
    yield commune
    database.session.execute(database.delete(LocalisationInterministerielle))
    database.session.execute(database.delete(Commune))
    database.session.commit()


@patch("app.tasks.refs.update_ref_communes.subtask")
def test_import_file_acv(mock_subtask: MagicMock, add_commune_la_gacilly):
    # DO
    with patch("shutil.move", return_value=None):  # ne pas supprimer le fichier de tests :)
        import_file_acv(_data / "acv.csv")

    commune = select_commune("35288")
    assert commune.is_acv is True
    assert commune.date_acv.strftime("%Y-%m-%d") == "2018-09-21"
