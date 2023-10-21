import logging
import dataclasses
from app import db
from app.models.financial.FinancialAe import FinancialAe as Ae
from app.models.tags.Tags import TagVO, TagAssociation
from app.models.tags.Tags import Tags as DbTag

logger = logging.getLogger(__name__)


def select_tags(tag: TagVO) -> DbTag:
    """
    Retourne l'objet DbTag à partir du type et de la valeur
    :param tag:    un tag value object
    :return:
    le Tag
    """
    stmt = db.select(DbTag)
    stmt = stmt.where(DbTag.type == tag.type)
    if tag.value is not None:
        stmt = stmt.where(DbTag.value == tag.value)

    return db.session.execute(stmt).scalar_one()


def _select_ae_having_tags(tag_id: int):
    """
    Retourne la selection d'ae qui ont déjà au moins un tag tag_id appliqué
    :param tag_id: l'id du tag
    :return:
    """
    return db.select(TagAssociation.financial_ae).where(TagAssociation.tag_id == tag_id).distinct()


@dataclasses.dataclass
class ApplyTags:
    tag: DbTag

    def apply_tags_ae(self, whereclause):
        """
        Applique un tag sur les Financial AE retournée par le statement passé en paramètre
        :param tag: le tag à appliquer
        :param where_clause: le filtrage
        :return:
        """
        stmt_ae = db.select(Ae.id).where(whereclause).where(Ae.id.not_in(_select_ae_having_tags(self.tag.id)))
        ae_ids = [row[0] for row in db.session.execute(stmt_ae).all()]

        if (
            ae_ids
        ):  # on vérifie que la liste des lignes à ajouter est non vide. Sinon pas besoin d'insert de nouvelle Assocations
            for ae_id in ae_ids:
                db.session.add(TagAssociation(financial_ae=ae_id, tag=self.tag, auto_applied=True))
            db.session.commit()
            logger.info(f"[TAGS][{self.tag.type}] Fin application auto du tags")
        else:
            logger.info(f"[TAGS][{self.tag.type}] Aucune nouvelle association détecté")
