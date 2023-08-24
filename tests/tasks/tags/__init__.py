import pytest

__all__ = ("insert_tags",)

from app.models.tags.Tags import Tags, TagAssociation


@pytest.fixture(scope="function")
def insert_tags(database):
    tag_fv = Tags(
        **{
            "type": "Fond vert",
            "value": None,
            "description": "Tag auto Fond Vert si programme = 380",
            "enable_rules_auto": True,
        }
    )
    tag_disable = Tags(
        **{
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
    database.session.execute(database.delete(TagAssociation))
    database.session.commit()
