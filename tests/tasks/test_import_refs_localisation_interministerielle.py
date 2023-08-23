import json
import os
from unittest.mock import patch, call

import pytest

from app import db
from app.models.refs.commune import Commune
from app.models.refs.localisation_interministerielle import LocalisationInterministerielle
from app.tasks.import_refs_tasks import import_refs_task
from app.tasks.refs import import_line_ref_localisation_interministerielle


@pytest.fixture(scope="module")
def add_comune_belley(database):
    commune_belley = Commune(**{"code": "01034", "label_commune": "Belley", "code_departement": "01"})
    database.session.add(commune_belley)
    database.session.commit()
    yield commune_belley
    database.session.execute(database.delete(Commune))


@pytest.fixture(scope="module")
def add_comune_angers(database):
    commune = Commune(**{"code": "0000", "label_commune": "Angers", "code_departement": "49"})
    database.session.add(commune)
    database.session.commit()
    yield commune
    database.session.execute(database.delete(Commune))


@patch("app.tasks.import_refs_tasks.subtask")
def test_import_refs_localisation_interministerielle(mock_subtask):
    import_refs_task(
        os.path.abspath(os.getcwd()) + "/data/LOC_INTERMIN_20230126.csv",
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
