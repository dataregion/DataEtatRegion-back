import pytest
from services.regions import sanitize_source_region_for_bdd_request


@pytest.mark.parametrize(
    "source_region, data_source, expected",
    [
        ("53", "REGION", "53"),
        ("053", "REGION", "53"),
        ("053", "NATION", "53"),
        (None, "NATION", None),
    ],
)
def test_sanitize_source_region_for_bdd_request(source_region, data_source, expected):
    sanitized = sanitize_source_region_for_bdd_request(source_region, data_source)
    assert sanitized == expected


@pytest.mark.parametrize(
    "source_region, data_source",
    [
        (None, "REGION"),
    ],
)
def test_ko_sanitize_source_region_for_bdd_request(source_region, data_source):
    with pytest.raises(ValueError):
        sanitize_source_region_for_bdd_request(source_region, data_source)
