import pytest

from app.models.tags.Tags import Tag

#region test tags app model

@pytest.mark.parametrize(
        "input,expected,expected_db_fullname",
        [
            ('type:value'   , Tag.from_typevalue('type', 'value')  , "type:value",),
            ('type:value:'  , Tag.from_typevalue('type', 'value')  , "type:value",),
            ('type:value:::', Tag.from_typevalue('type', 'value')  , "type:value",),
            ('type:'        , Tag.from_typevalue('type', None)     , "type:"     ,),
            ('type'         , Tag.from_typevalue('type', None)     , "type:"     ,),
        ]
)
def test_parse_tags_prettyname(input: str, expected: Tag, expected_db_fullname: str):
    """Test parsing of tags pretty name"""
    tag_candidate = Tag.from_prettyname(input)
    assert tag_candidate == expected

    assert expected_db_fullname == tag_candidate.db_fullname

    sanitized_candidate = Tag.sanitize_str(input)
    assert expected_db_fullname == sanitized_candidate

@pytest.mark.parametrize(
        "input,err_type",
        [
            (''   , Exception),
        ]
)
def test_parse_tags_prettyname_error(input: str, err_type):
    """Test parsing of tags pretty name"""
    with pytest.raises(err_type) as e:
        _ = Tag.from_prettyname(input)

#endregion