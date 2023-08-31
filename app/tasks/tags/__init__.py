import dataclasses

from app.models.tags.Tags import TagAssociation, Tags
from app.models.financial.FinancialAe import FinancialAe as Ae
from ... import db
import logging

LOGGER = logging.getLogger()


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


@dataclasses.dataclass
class ApplyTags:
    tag: Tags

    def apply_tags_ae(self, whereclause):
        """
        Applique un tag sur les Financial AE retournée par le statement passé en paramètre
        :param tag: le tag à appliquer
        :param where_clause: le filtrage
        :return:
        """
        stmt_ae = db.select(Ae.id).where(whereclause).where(Ae.id.not_in(select_ae_have_tags(self.tag.id)))
        ae_ids = [row[0] for row in db.session.execute(stmt_ae).all()]

        if (
            ae_ids
        ):  # on vérifie que la liste des lignes à ajouter est non vide. Sinon pas besoin d'insert de nouvelle Assocations
            for ae_id in ae_ids:
                db.session.add(TagAssociation(financial_ae=ae_id, tag=self.tag, auto_applied=True))
            db.session.commit()
            LOGGER.info(f"[TAGS][{self.tag.type}] Fin application auto du tags")
        else:
            LOGGER.info(f"[TAGS][{self.tag.type}] Aucune nouvelle association détecté")


from .apply_tags import *
from .update_all_tags import *
