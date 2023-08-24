from unittest.mock import patch, call
import pytest

from app.models.tags.Tags import Tags
from . import *  # necessaire pour utiliser la fixture dans le init
from app.tasks.tags.update_all_tags import update_all_tags


@pytest.fixture(scope="module")
def tags(database):
    database.session.add(Tags(**TAG_FOND_VERT))
    database.session.add(Tags(**TAG_RELANCE))
    database.session.add(Tags(**TAG_DISABLE_AUTO))
    database.session.commit()
    yield
    database.session.execute(database.delete(Tags))
    database.session.commit()


@patch("app.tasks.tags.update_all_tags.subtask")
def test_update_tags_enable_auto(mock_subtask, tags):
    # DO
    update_all_tags()

    mock_subtask.ass("apply_tags_fond_vert")
    mock_subtask.assert_has_calls([call("apply_tags_fond_vert")])
    # raises AssertionError si le tag test est appelé
    with pytest.raises(AssertionError):
        mock_subtask.assert_called_with("apply_tags_test")
