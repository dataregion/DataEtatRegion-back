import json
from unittest.mock import patch, call

from app import db
from models.entities.refs.CodeProgramme import CodeProgramme
from models.entities.refs.Ministere import Ministere
from app.tasks.import_refs_tasks import import_refs_task
from app.tasks.refs import import_line_one_ref_default
from tests import TESTS_PATH

_data = TESTS_PATH / "data"


@patch("app.tasks.import_refs_tasks.subtask")
def test_import_refs_code_programme(mock_subtask):
    # DO
    import_refs_task(
        _data / "Calculette_Chorus_test.xlsx",
        "CodeProgramme",
        ["code_ministere", "code", "label"],
        is_csv=False,
        usecols=[0, 2, 3],
        sheet_name="03 - Programmes",
        skiprows=8,
    )

    mock_subtask.assert_has_calls(
        [
            call().delay(
                model_name="CodeProgramme",
                data='{"code_ministere":"MIN01","code":"0105","label":"Action de la France en Europe et dans le monde"}',
            ),
            call().delay(
                model_name="CodeProgramme",
                data='{"code_ministere":"MIN01","code":"0151","label":"Fran\\u00e7ais \\u00e0 l\'\\u00e9tranger et affaires consulaires"}',
            ),
            call().delay(
                model_name="CodeProgramme",
                data='{"code_ministere":"MIN01","code":"0185","label":"Diplomatie culturelle et d\'influence"}',
            ),
            call("import_line_one_ref_default"),
        ],
        any_order=True,
    )


@patch("app.tasks.import_refs_tasks.subtask")
def test_import_refs_ministere(mock_subtask):
    import_refs_task(
        _data / "Calculette_Chorus_test.xlsx",
        "Ministere",
        ["code", "sigle_ministere", "label"],
        is_csv=False,
        usecols=[0, 1, 2],
        sheet_name="02 - Ministères",
        skiprows=8,
    )

    mock_subtask.assert_has_calls(
        [
            call().delay(
                model_name="Ministere",
                data='{"code":"MIN01","sigle_ministere":"MEAE","label":"Europe&Aff.\\u00c9trang\\u00e8res"}',
            ),
            call("import_line_one_ref_default"),
        ],
        any_order=True,
    )


def test_import_insert_code_programme_line(session):
    refmin = Ministere(**{"code": "MIN01", "label": "MIN01"})
    session.add(refmin)
    session.commit()

    import_line_one_ref_default(
        "CodeProgramme",
        json.dumps({"code": "0185", "label": "Diplomatie culturelle et d'influence", "code_ministere": "MIN01"}),
    )
    import_line_one_ref_default(
        "CodeProgramme", json.dumps({"code_ministere": "MIN01", "code": "151", "label": "TEST"})
    )
    d_to_update = session.execute(db.select(CodeProgramme).filter_by(code="185")).scalar_one_or_none()
    assert d_to_update.label == "Diplomatie culturelle et d'influence"

    d_to_update = session.execute(db.select(CodeProgramme).filter_by(code="151")).scalar_one_or_none()
    assert d_to_update.label == "TEST"


def test_update_code_programme(session):
    # GIVEN
    bop = {
        "code": "754",
    }
    ministere = {"code": "MIN09", "label": "label MIN09"}
    session.add(Ministere(**ministere))
    session.add(CodeProgramme(**bop))
    session.commit()

    # DO
    import_line_one_ref_default(
        "CodeProgramme", '{"code_ministere":"MIN09","code":"0754","label":"Contribution collectivites territoriales"}'
    )

    d_to_update = session.execute(db.select(CodeProgramme).filter_by(code="754")).scalar_one_or_none()
    assert d_to_update.code_ministere == "MIN09"
    assert d_to_update.label == "Contribution collectivites territoriales"
