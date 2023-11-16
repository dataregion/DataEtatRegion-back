import json

import pytest

from app.models.refs.qpv import Qpv


@pytest.fixture(scope="function")
def insert_qpv(session):
    qpv01 = {"code": "QP093009", "label": "Le Plateau - Les Malassis - La Noue", "label_commune": "Montreuil"}
    qpv02 = {"code": "QP083007", "label": "Quartiers Nord Est", "label_commune": "Avignon"}
    qpv03 = {
        "code": "QP093018",
        "label": "Bel Air - Grands Pêchers - Ruffins - Le Morillon",
        "label_commune": "Montreuil",
    }

    session.add(Qpv(**qpv01))
    session.add(Qpv(**qpv02))
    session.add(Qpv(**qpv03))

    return [qpv01, qpv02, qpv03]


def test_qpv_by_code(test_client, insert_qpv):
    code = "QP093009"
    resp = test_client.get("/budget/api/v1/qpv/" + code)
    assert resp.status_code == 200
    min_return = json.loads(resp.data.decode())
    assert min_return == insert_qpv[0]


def test_qpv_not_found(test_client, insert_qpv):
    # GIVEN
    code_not_found = "code_not_found"
    resp = test_client.get("/budget/api/v1/qpv/" + code_not_found)
    assert resp.status_code == 404


def test_search_qpv_no_content(test_client, insert_qpv):
    test = "fQP09"
    resp = test_client.get("/budget/api/v1/qpv?code=" + test)
    assert resp.status_code == 204


def test_search_min_by_commune(test_client, insert_qpv):
    test = "Avign"
    resp = test_client.get("/budget/api/v1/qpv?label_commune=" + test)
    assert resp.status_code == 200

    page_return = json.loads(resp.data.decode())
    assert page_return["items"].__len__() == 1
    assert page_return["pageInfo"] == {"totalRows": 1, "page": 1, "pageSize": 100}
    assert page_return["items"][0] == insert_qpv[1]
