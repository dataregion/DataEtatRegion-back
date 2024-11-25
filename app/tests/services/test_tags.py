import pytest

from models.value_objects.tags import TagVO

# region test TagVO


@pytest.mark.parametrize(
    "input,expected,expected_db_fullname",
    [
        (
            "type:value",
            TagVO.from_typevalue("type", "value"),
            "type:value",
        ),
        (
            "type:value:",
            TagVO.from_typevalue("type", "value"),
            "type:value",
        ),
        (
            "type:value:::",
            TagVO.from_typevalue("type", "value"),
            "type:value",
        ),
        (
            "type:",
            TagVO.from_typevalue("type", None),
            "type:",
        ),
        (
            "type",
            TagVO.from_typevalue("type", None),
            "type:",
        ),
    ],
)
def test_parse_tags_prettyname(input: str, expected: TagVO, expected_db_fullname: str):
    """Test parsing of tags pretty name"""
    tag_candidate = TagVO.from_prettyname(input)
    assert tag_candidate == expected

    assert expected_db_fullname == tag_candidate.fullname

    sanitized_candidate = TagVO.sanitize_str(input)
    assert expected_db_fullname == sanitized_candidate


@pytest.mark.parametrize(
    "input,err_type",
    [
        ("", Exception),
        (None, Exception),
    ],
)
def test_parse_tags_prettyname_error(input: str, err_type):
    """Test parsing of tags pretty name"""
    with pytest.raises(err_type) as _:
        _ = TagVO.from_prettyname(input)


# endregion
