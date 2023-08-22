__all__ = ("update_all_tags", "apply_tags")

from app import db
from app.models.tags.Tags import TagAssociation


def select_ae_have_tags():
    """
    Retourne la selection d'ae qui ont déjà au moins un tag
    :return:
    """
    # TODO
    return db.select(TagAssociation.association_id).distinct()
