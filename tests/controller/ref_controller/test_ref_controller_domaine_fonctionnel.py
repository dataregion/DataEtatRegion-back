import json

import pytest
from app.models.refs.domaine_fonctionnel import DomaineFonctionnel


@pytest.fixture(scope="module")
def insert_domaine_fonctionnel(database):
    data = []

    for i in range(10):
        domaine = {
            "code": f"00{i + 1}0",
            "label": f"domaine 0{i + 1}",
            "description": f"description du domaine {i + 1}",
        }
        database.session.add(DomaineFonctionnel(**domaine))
        data.append(domaine)
    database.session.commit()
    yield data
    database.session.execute(database.delete(DomaineFonctionnel))


def test_domaine_by_code(test_client, insert_domaine_fonctionnel):
    code = "0030"
    resp = test_client.get("/budget/api/v1/domaine-fonct/" + code)
    assert resp.status_code == 200
    domaine_return = json.loads(resp.data.decode())
    assert domaine_return == {
        "code": code,
        "label": "domaine 03",
        "description": "description du domaine 3",
        "code_programme": "030",
    }


def test_domaine_not_found(test_client, insert_domaine_fonctionnel):
    # GIVEN
    code_not_found = "code_not_found"
    resp = test_client.get("/budget/api/v1/domaine-fonct/" + code_not_found)
    assert resp.status_code == 404


def test_search_domaine_no_content(test_client, insert_domaine_fonctionnel):
    test = "daine 02"
    resp = test_client.get("/budget/api/v1/domaine-fonct?code=" + test)
    assert resp.status_code == 204


def test_search_domaine_by_label(test_client, insert_domaine_fonctionnel):
    test = "aine 01"
    resp = test_client.get("/budget/api/v1/domaine-fonct?code=" + test + "&label=" + test)
    assert resp.status_code == 200

    page_return = json.loads(resp.data.decode())
    assert page_return["items"].__len__() == 2
    assert page_return["items"][0]["code"] == "0010"
    assert page_return["items"][1]["code"] == "00100"

    assert page_return["pageInfo"] == {"totalRows": 2, "page": 1, "pageSize": 100}
