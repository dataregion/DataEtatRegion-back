import pytest

__all__ = ("insert_tags",)

from app.models.tags.Tags import Tags


@pytest.fixture(scope="module")
def insert_tags(database):
    tag_fv = Tags(
        **{
            "id": 1,
            "type": "Fond vert",
            "value": None,
            "description": "Tag auto Fond Vert si programme = 380",
            "enable_rules_auto": True,
        }
    )
    tag_disable = Tags(
        **{
            "id": 2,
            "type": "test",
            "value": None,
            "description": "tag non actif",
            "enable_rules_auto": False,
        }
    )

    database.session.add(tag_fv)
    database.session.add(tag_disable)
    database.session.commit()
    yield {"fond_vert": tag_fv, "disabled": tag_disable}
    database.session.execute(database.delete(Tags))
    database.session.commit()
