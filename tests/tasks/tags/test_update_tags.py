from unittest.mock import patch

import pytest
from . import *  # necessaire pour utiliser la fixture dans le init
from app.tasks.tags.update_all_tags import update_all_tags


@patch("app.tasks.tags.update_all_tags.subtask")
def test_update_tags_enable_auto(mock_subtask, insert_tags):
    # DO
    update_all_tags()

    mock_subtask.assert_called_once_with("apply_tags_fond_vert")
    # raises AssertionError si le tag test est appelé
    with pytest.raises(AssertionError):
        mock_subtask.assert_called_with("apply_tags_test")
