import json

import pytest

from app.models.refs.groupe_marchandise import GroupeMarchandise


@pytest.fixture(scope="module")
def insert_gm(database):
    gm_1 = {
        "code": "01.01",
        "segment": "FRAIS POSTAUX",
        "domaine": " FRAIS1",
        "code_pce": "code_pce",
        "label_pce": "label_pce",
        "label": "EX-AI EXPÉDITION",
        "description": "description 0101",
    }
    gm_2 = {
        "code": "01.01.02",
        "segment": "Impression",
        "domaine": " FRAIS2",
        "code_pce": "code_pce",
        "label_pce": "label_pce",
        "label": "EX-AI IMPRESSIONS",
    }
    gm_3 = {
        "code": "02.01.02",
        "segment": "impression",
        "domaine": " informatique",
        "code_pce": "code_pce",
        "label_pce": "label_pce",
        "label": "EX-IT ACHAT DE COPIE",
    }
    database.session.add(GroupeMarchandise(**gm_1))
    database.session.add(GroupeMarchandise(**gm_2))
    database.session.add(GroupeMarchandise(**gm_3))
    database.session.commit()
    yield [gm_1, gm_2, gm_3]
    database.session.execute(database.delete(GroupeMarchandise))


def test_gm_by_code(test_client, insert_gm):
    code = "01.01"
    resp = test_client.get("/budget/api/v1/groupe-marchandise/" + code)
    assert resp.status_code == 200
    domaine_return = json.loads(resp.data.decode())
    assert domaine_return == insert_gm[0]


def test_gm_not_found(test_client, insert_gm):
    # GIVEN
    code_not_found = "code_not_found"
    resp = test_client.get("/budget/api/v1/groupe-marchandise/" + code_not_found)
    assert resp.status_code == 404


def test_search_gm_no_content(test_client, insert_gm):
    test = "daine 02"
    resp = test_client.get("/budget/api/v1/groupe-marchandise?query=" + test)
    assert resp.status_code == 204


def test_search_gm_by_domaine(test_client, insert_gm):
    test = "frais"
    resp = test_client.get("/budget/api/v1/groupe-marchandise?query=" + test)
    assert resp.status_code == 200

    page_return = json.loads(resp.data.decode())
    assert page_return["items"].__len__() == 2
    assert page_return["items"][0]["code"] == "01.01"
    assert page_return["items"][1]["code"] == "01.01.02"

    assert page_return["pageInfo"] == {"totalRows": 2, "page": 1, "pageSize": 100}
