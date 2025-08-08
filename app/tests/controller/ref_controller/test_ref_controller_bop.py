import json
from . import *  # noqa: F403


def test_bop_by_code(test_client, init_ref_ministeres_themes):
    code = "BOP2"
    resp = test_client.get("/budget/api/v1/programme/" + code)
    assert resp.status_code == 200
    bop_return = json.loads(resp.data.decode())
    assert bop_return == {
        "code": "BOP2",
        "code_ministere": "MIN02",
        "code_theme": "TH2",
        "label_theme": "theme 02",
        "description": "description du bop 2",
        "label": "label programme 2",
        "grist_row_id": None,
        "is_deleted": False,
        "synchro_grist_id": None,
    }


def test_bop_not_found(test_client, init_ref_ministeres_themes):
    # GIVEN
    code_not_found = "code_not_found"
    resp = test_client.get("/budget/api/v1/programme/" + code_not_found)
    assert resp.status_code == 404


def test_search_bop_no_content(test_client, init_ref_ministeres_themes):
    test = "fcode1"
    resp = test_client.get("/budget/api/v1/programme?query=" + test)
    assert resp.status_code == 204


def test_search_bop_bycode_label(test_client, init_ref_ministeres_themes):
    test = "programme 1"
    resp = test_client.get("/budget/api/v1/programme?query=" + test)
    assert resp.status_code == 200

    page_return = json.loads(resp.data.decode())
    assert page_return["items"].__len__() == 2
    assert page_return["pageInfo"] == {"totalRows": 2, "page": 1, "pageSize": 100}
