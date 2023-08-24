__all__ = ("update_all_tags", "apply_tags")

from app import db
from app.models.tags.Tags import TagAssociation, Tags


def select_ae_have_tags(tag_id):
    """
    Retourne la selection d'ae qui ont déjà au moins un tag tag_id appliqué
    :param tag_id: l'id du tag
    :return:
    """
    return db.select(TagAssociation.financial_ae).where(TagAssociation.tag_id == tag_id).distinct()


def select_tag(tag_type: str, tag_value: str | None = None) -> Tags:
    """
    Retourne l'objet Tags à partir du type et de la valeur
    :param tag_type:    le type du tag
    :param tag_value:   la valeur du tag. Par défaut None
    :return:
    le Tag
    """
    return db.session.execute(db.select(Tags).where(Tags.type == tag_type).where(Tags.value == tag_value)).scalar_one()
