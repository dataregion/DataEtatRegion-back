from tests import _assert_can_jsonize

from services.qpv.colonnes import get_list_colonnes_tableau

from fastapi.testclient import TestClient


####
#
def test_get_list_colonnes_tableau_is_serializable():
    colonnes = get_list_colonnes_tableau()
    assert colonnes is not None
    dumped = _assert_can_jsonize(colonnes, mode="json")
    assert dumped is not None


def test_get_list_colonnes_grouping_is_serializable():
    colonnes = get_list_colonnes_grouping()
    assert colonnes is not None
    dumped = _assert_can_jsonize(colonnes, mode="json")
    assert dumped is not None
