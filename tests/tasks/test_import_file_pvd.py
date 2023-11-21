import json

from datetime import datetime
from unittest.mock import patch, call, ANY, MagicMock

import pytest

from app.models.refs.commune import Commune
from app.tasks.refs.import_ref_communes_pvd import import_line_pvd, import_file_pvd
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
            "date_pvd": datetime.now(),
        }
    )
    database.session.add(commune)
    database.session.commit()
    yield commune
    database.session.execute(database.delete(Commune))
    database.session.commit()


@pytest.fixture(scope="function")
def add_commune_cancale(database):
    commune = Commune(
        **{
            "code": "35049",
            "label_commune": "Cancale",
            "code_departement": "35",
            "is_pvd": False,
            "date_pvd": datetime.now(),
        }
    )
    database.session.add(commune)
    database.session.commit()
    yield commune
    database.session.execute(database.delete(Commune))
    database.session.commit()


@patch("app.tasks.refs.import_ref_communes_pvd.subtask")
def test_import_file_pvd(mock_subtask: MagicMock, add_commune_la_gacilly):
    # DO
    with patch("shutil.move", return_value=None):  # ne pas supprimer le fichier de tests :)
        import_file_pvd(_data / "pvd.csv")

    mock_subtask.assert_has_calls(
        [
            call().delay(
                '{"insee_com":"56061","lib_com":"La Gacilly","id_pvd":"pvd-53-56-6","date_signature":"2021-07-09"}',
                ANY,
            ),
            call("import_line_pvd"),
        ],
        any_order=True,
    )


def test_import_line_pvd(database, session, add_commune_cancale):
    # GIVEN
    data = json.loads('{"insee_com":"35049","lib_com":"Cancale","id_pvd":"pvd-53-35-30","date_signature": null}')

    import_line_pvd(data, tech_info_list=("a task id", 1))

    # ASSERT
    data = session.execute(database.select(Commune).where(Commune.code == "35049")).scalar_one_or_none()
    assert data.id is not None
    assert data.is_pvd is True
    assert data.date_pvd is None
