from unittest.mock import patch, call, ANY

import pytest

from app.models.tags.Tags import Tags
from app.tasks.tags.update_all_tags import update_all_tags


@pytest.fixture(scope="module")
def tags(test_db):
    tag_fv = {
        "type": "Fond vert",
        "value": None,
        "description": "Tag auto Fond Vert si programme = 380",
        "enable_rules_auto": True,
    }
    tag_disable = {
        "type": "test",
        "value": None,
        "description": "tag non actif",
        "enable_rules_auto": False,
    }

    test_db.session.add(Tags(**tag_fv))
    test_db.session.add(Tags(**tag_disable))
    test_db.session.commit()


@patch("app.tasks.tags.update_all_tags.subtask")
def test_update_tags_enable_auto(mock_subtask, tags):
    # DO
    update_all_tags()

    mock_subtask.assert_called_once_with("apply_tags_fond_vert")
    # raises AssertionError si le tag test est appelé
    with pytest.raises(AssertionError):
        mock_subtask.assert_called_with("apply_tags_test")
