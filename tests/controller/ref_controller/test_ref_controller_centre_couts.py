import json

from . import *  # noqa: F403


def test_centre_cout_by_code(test_client, insert_centre_couts):
    code = insert_centre_couts[0]["code"]
    resp = test_client.get("/budget/api/v1/centre-couts/" + code)
    assert resp.status_code == 200
    cc_return = json.loads(resp.data.decode())
    assert cc_return == insert_centre_couts[0]


def test_centre_cout_by_code_not_found(test_client, insert_centre_couts):
    # GIVEN
    code_not_found = "code_not_found"
    resp = test_client.get("/budget/api/v1/centre-couts/" + code_not_found)
    assert resp.status_code == 404


def test_search_centre_cout_no_content(test_client, insert_centre_couts):
    test = "fcode1"
    resp = test_client.get("/budget/api/v1/centre-couts?code=" + test)
    assert resp.status_code == 204


def test_search_centre_cout_bycode_label(test_client, insert_centre_couts):
    test = "code12"
    resp = test_client.get("/budget/api/v1/centre-couts?code=" + test + "&label=" + test)
    assert resp.status_code == 200

    page_return = json.loads(resp.data.decode())
    assert page_return["items"].__len__() == 2
    assert insert_centre_couts[11] in page_return["items"]
    assert insert_centre_couts[12] in page_return["items"]
    assert page_return["pageInfo"] == {"totalRows": 2, "page": 1, "pageSize": 100}


def test_search_centre_cout_bycode(test_client, insert_centre_couts):
    test = "code1"
    resp = test_client.get("/budget/api/v1/centre-couts?code=" + test + "&limit=5&page_number=0")
    resp_page2 = test_client.get("/budget/api/v1/centre-couts?code=" + test + "&limit=5&page_number=2")

    assert resp.status_code == 200
    assert resp_page2.status_code == 200

    page1_return = json.loads(resp.data.decode())
    page2_return = json.loads(resp_page2.data.decode())
    assert page1_return["items"].__len__() == 5
    assert page2_return["items"].__len__() == 5

    assert insert_centre_couts[0] in page1_return["items"]  # code1
    assert insert_centre_couts[9] in page1_return["items"]  # code10
    assert insert_centre_couts[10] in page1_return["items"]  # code11
    assert insert_centre_couts[11] in page1_return["items"]  # code12
    assert insert_centre_couts[12] in page1_return["items"]  # code13

    assert insert_centre_couts[13] in page2_return["items"]  # code14
    assert insert_centre_couts[14] in page2_return["items"]  # code15
    assert insert_centre_couts[15] in page2_return["items"]  # code16
    assert insert_centre_couts[16] in page2_return["items"]  # code17

    assert page1_return["pageInfo"] == {"totalRows": 11, "page": 1, "pageSize": 5}
    assert page2_return["pageInfo"] == {"totalRows": 11, "page": 2, "pageSize": 5}


def test_search_centre_cout_by_code_postal(test_client, insert_centre_couts):
    test = "35411"
    resp = test_client.get("/budget/api/v1/centre-couts?code_postal=" + test + "&limit=5&pageNumber=0")
    assert resp.status_code == 200
    page_return = json.loads(resp.data.decode())
    assert page_return["items"].__len__() == 1
    assert insert_centre_couts[10] in page_return["items"]  # code11
