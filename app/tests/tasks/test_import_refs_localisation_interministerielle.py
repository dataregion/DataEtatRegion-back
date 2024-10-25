import json
from unittest.mock import patch, call

import pytest

from models.entities.refs.Commune import Commune
from models.entities.refs.LocalisationInterministerielle import LocalisationInterministerielle
from app.tasks.import_refs_tasks import import_refs_task
from app.tasks.refs import import_line_ref_localisation_interministerielle
from tests import TESTS_PATH

_data = TESTS_PATH / "data"


@pytest.fixture(scope="function")
def add_comune_belley(database):
    commune_belley = database.session.query(Commune).filter_by(code="01035").one_or_none()

    if not commune_belley:
        commune_belley = Commune(**{"code": "01035", "label_commune": "Belley", "code_departement": "01"})
        database.session.add(commune_belley)
        database.session.commit()

    yield commune_belley
    database.session.execute(database.delete(Commune))
    database.session.commit()


@pytest.fixture(scope="function")
def add_comune_angers(database):
    commune = database.session.query(Commune).filter_by(code="0000").one_or_none()

    if not commune:
        commune = Commune(**{"code": "0000", "label_commune": "Angers", "code_departement": "49"})
        database.session.add(commune)
        database.session.commit()

    yield commune
    database.session.execute(database.delete(Commune))
    database.session.commit()


@patch("app.tasks.import_refs_tasks.subtask")
def test_import_refs_localisation_interministerielle(mock_subtask):
    import_refs_task(
        _data / "LOC_INTERMIN_20230126.csv",
        "LocalisationInterministerielle",
        ["code", "niveau", "code_departement", "commune", "site", "code_parent", "label"],
        usecols=[0, 1, 3, 5, 6, 9, 10],
        sep=";",
    )

    mock_subtask.assert_has_calls(
        [
            call().delay(
                model_name="LocalisationInterministerielle",
                data='{"code":"B100000","niveau":"BATIMENT","code_departement":"30","commune":"N\\u00eemes","site":"CASERNE MAJOR SOLER","code_parent":"S120594","label":"ATELIER DE REPARATION ET D\'ENTRETIEN BAT 3"}',
            ),
            call("import_line_one_ref_LocalisationInterministerielle"),
        ],
        any_order=True,
    )


def test_import_insert_localisation(database, session, add_comune_belley):
    import_line_ref_localisation_interministerielle(
        data=json.dumps(
            {
                "code": "B100000",
                "niveau": "NATIONAL",
                "code_departement": "01",
                "commune": "BELLEY",
                "site": "CASERNE MAJOR SOLER",
                "code_parent": "S120594",
                "label": "ATELIER DE REPARATION ET D'ENTRETIEN BAT 3",
            }
        )
    )
    d_to_update = session.execute(
        database.select(LocalisationInterministerielle).filter_by(code="B100000")
    ).scalar_one_or_none()
    assert d_to_update.commune.label_commune == "Belley"
    assert d_to_update.commune_id == add_comune_belley.id
    assert d_to_update.site == "CASERNE MAJOR SOLER"
    assert d_to_update.niveau == "NATIONAL"
    assert d_to_update.code_parent == "S120594"

    database.session.execute(database.delete(LocalisationInterministerielle))
    database.session.commit()


def test_import_insert_localisation_inter_exist(app, database, add_comune_belley, add_comune_angers):
    # WHEN Insert loc inter à Belley

    loc = LocalisationInterministerielle(
        **{
            "code": "B215151",
            "niveau": "to_update",
            "label": "to_update",
        }
    )
    loc.commune = add_comune_belley
    database.session.add(loc)
    database.session.commit()

    # DO
    import_line_ref_localisation_interministerielle(
        data=json.dumps(
            {
                "code": loc.code,
                "niveau": "NATIONAL",
                "code_departement": "49",
                "commune": "Angers",
                "site": "CASERNE SOLER",
                "code_parent": "XXXX",
                "label": "TEST ATELIER DE REPARATION ET D'ENTRETIEN BAT 3",
            }
        )
    )

    with app.app_context():  # necessaire dans le contexte de l'app flask pour
        d_to_update = database.session.execute(
            database.select(LocalisationInterministerielle).filter_by(code=loc.code)
        ).scalar_one_or_none()
        assert d_to_update.commune.label_commune == "Angers"
        assert d_to_update.commune_id == add_comune_angers.id
        assert d_to_update.site == "CASERNE SOLER"
        assert d_to_update.niveau == "NATIONAL"
        assert d_to_update.code_parent == "XXXX"

    database.session.execute(database.delete(LocalisationInterministerielle))
    database.session.commit()


def test_import_insert_localisation_interministerielle_niveau_commune(database, session, add_comune_belley):
    # DO
    import_line_ref_localisation_interministerielle(
        data=json.dumps(
            {
                "code": "N8401035",
                "niveau": "COMMUNE",
                "code_departement": None,
                "commune": None,
                "site": "site commune",
                "code_parent": "N84",
                "label": "test",
            }
        )
    )
    # ASSERT
    d_to_update = session.execute(
        database.select(LocalisationInterministerielle).filter_by(code="N8401035")
    ).scalar_one_or_none()

    assert d_to_update.commune.label_commune == "Belley"
    assert d_to_update.commune_id == add_comune_belley.id
    assert d_to_update.niveau == "COMMUNE"
    assert d_to_update.code_parent == "N84"

    database.session.execute(database.delete(LocalisationInterministerielle))
    database.session.commit()
