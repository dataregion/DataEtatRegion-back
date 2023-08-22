import pytest


__all__ = ('insert_tags',)

from app.models.tags.Tags import Tags


@pytest.fixture(scope="package")
def insert_tags(test_db):
    tag_fv = Tags(**{
        "id": 1,
        "type": "Fond vert",
        "value": None,
        "description": "Tag auto Fond Vert si programme = 380",
        "enable_rules_auto": True,
    })
    tag_disable = Tags(**{
        "id":2,
        "type": "test",
        "value": None,
        "description": "tag non actif",
        "enable_rules_auto": False,
    })

    test_db.session.add(tag_fv)
    test_db.session.add(tag_disable)
    test_db.session.commit()
    return [tag_fv, tag_disable]
