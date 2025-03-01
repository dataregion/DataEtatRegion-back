import json

import pytest

from models.entities.refs.Commune import Commune
from models.entities.refs.LocalisationInterministerielle import LocalisationInterministerielle


@pytest.fixture(scope="module")
def insert_loc(database):
    commune_nime = Commune(**{"code": "001", "label_commune": "Nîmes", "code_departement": "30"})
    commune_rennes = Commune(**{"code": "002", "label_commune": "Rennes", "code_departement": "35"})
    commune_change = Commune(**{"code": "003", "label_commune": "Change", "code_departement": "72"})

    loc_1 = LocalisationInterministerielle(
        **{
            "code": "B100001",
            "label": "ATELIER",
            "site": "CASERNE MAJOR SOLER",
            "niveau": "BATIMENT",
            "code_parent": "S120594",
        }
    )

    loc_2 = LocalisationInterministerielle(
        **{"code": "S120594", "label": "parent", "site": "site parent", "niveau": "TERRAIN", "code_parent": None}
    )

    loc_3 = LocalisationInterministerielle(
        **{
            "code": "B100002",
            "label": "site label rennes",
            "site": "site rennest",
            "niveau": "BATIMENT",
            "code_parent": "N",
            "description": "description",
        }
    )

    loc_4 = LocalisationInterministerielle(
        **{
            "code": "B200001",
            "label": "ECOLE",
            "site": "site Change",
            "niveau": "REGION",
            "code_parent": "S120594",
        }
    )

    database.session.add(commune_nime)
    database.session.add(commune_rennes)
    database.session.add(commune_change)
    loc_1.commune = commune_nime
    loc_2.commune = commune_nime
    loc_3.commune = commune_rennes
    loc_4.commune = commune_change

    database.session.add(loc_1)
    database.session.add(loc_2)
    database.session.add(loc_3)
    database.session.add(loc_4)

    database.session.commit()
    yield [loc_1, loc_2, loc_3, loc_4]
    database.session.execute(database.delete(LocalisationInterministerielle))
    database.session.execute(database.delete(Commune))


def test_loc_inter_by_code(test_client, insert_loc):
    code = "B100002"
    resp = test_client.get("/budget/api/v1/loc-interministerielle/" + code)
    assert resp.status_code == 200
    domaine_return = json.loads(resp.data.decode())
    assert domaine_return["code"] == insert_loc[2].code
    assert domaine_return["commune"]["label_commune"] == "Rennes"


def test_loc_inter_not_found(test_client, insert_loc):
    # GIVEN
    code_not_found = "code_not_found"
    resp = test_client.get("/budget/api/v1/loc-interministerielle/" + code_not_found)
    assert resp.status_code == 404


def test_search_loc_inter_no_content(test_client, insert_loc):
    test = "notfound"
    resp = test_client.get("/budget/api/v1/loc-interministerielle?query=" + test)
    assert resp.status_code == 204


def test_search_loc_inter_by_site(test_client, insert_loc):
    test = "rennest"
    resp = test_client.get("/budget/api/v1/loc-interministerielle?limit=2&site=" + test)
    assert resp.status_code == 200

    page_return = json.loads(resp.data.decode())
    assert page_return["items"].__len__() == 1
    assert page_return["items"][0]["code"] == "B100002"
    assert page_return["items"][0]["site"] == "site rennest"

    assert page_return["pageInfo"] == {"totalRows": 1, "page": 1, "pageSize": 2}


def test_search_loc_inter_by_code_parent(test_client, insert_loc):
    code = "S120594"
    resp = test_client.get("/budget/api/v1/loc-interministerielle/" + code + "/loc-interministerielle?limit=20")
    assert resp.status_code == 200

    page_return = json.loads(resp.data.decode())
    assert page_return["items"].__len__() == 2
    assert page_return["items"][0]["code"] == "B100001"
    assert page_return["items"][1]["code"] == "B200001"

    assert page_return["pageInfo"] == {"totalRows": 2, "page": 1, "pageSize": 20}


def test_search_loc_inter_by_code_parent_not_found(test_client, insert_loc):
    code = "not_exist"
    resp = test_client.get("/budget/api/v1/loc-interministerielle/" + code + "/loc-interministerielle?limit=20")
    assert resp.status_code == 204
