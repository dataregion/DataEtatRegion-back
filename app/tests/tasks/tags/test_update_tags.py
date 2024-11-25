from unittest.mock import patch, call
import pytest

from models.entities.common.Tags import Tags
from . import *  # noqa: F403
from app.tasks.tags.update_all_tags import update_all_tags


@pytest.fixture(scope="module")
def tags(database):
    database.session.add(Tags(**TAG_FOND_VERT))  # noqa: F405
    database.session.add(Tags(**TAG_RELANCE))  # noqa: F405
    database.session.add(Tags(**TAG_DISABLE_AUTO))  # noqa: F405
    database.session.add(Tags(**TAG_CPER_21_27))  # noqa: F405
    database.session.add(Tags(**TAG_PVD))  # noqa: F405
    database.session.commit()
    yield
    database.session.execute(database.delete(Tags))
    database.session.commit()


@patch("app.tasks.tags.update_all_tags.subtask")
def test_update_tags_enable_auto(mock_subtask, tags):
    # DO
    update_all_tags()

    mock_subtask.assert_has_calls([call("apply_tags_fonds_vert"), call("apply_tags_cper_2021_27")], any_order=True)
    # raises AssertionError si le tag test est appelé
    with pytest.raises(AssertionError):
        mock_subtask.assert_called_with("apply_tags_test")
