import dataclasses
import logging

from app import celeryapp, db
from app.models.financial.FinancialAe import FinancialAe as Ae
from app.models.tags.Tags import TagAssociation, Tags
from . import select_ae_have_tags, select_tag
from ...models.refs.code_programme import CodeProgramme

celery = celeryapp.celery
LOGGER = logging.getLogger()


__all__ = ("apply_tags_fond_vert", "apply_tags_relance")


@celery.task(bind=True, name="apply_tags_fond_vert")
def apply_tags_fond_vert(self, tag_type: str, _tag_value: str | None):
    """
    Applique les tags Fond Vert
    :param self:
    :param tag_type: le nom du type tag
    :param _tag_value: la valeur du tag
    :return:
    """
    LOGGER.info("[TAGS][Fond vert] Application auto du tags fond vert")
    tag = select_tag(tag_type)
    LOGGER.debug(f"[TAGS][Fond vert] Récupération du tag fond vert id : {tag.id}")

    apply_task = ApplyTags(tag)
    apply_task.apply_tags_ae(Ae.programme == "380")


@celery.task(bind=True, name="apply_tags_relance")
def apply_tags_relance(self, tag_type: str, _tag_value: str | None):
    """
    Applique les tags Fond Vert
    :param self:
    :param tag_type: le nom du type tag
    :param _tag_value: la valeur du tag
    :return:
    """
    LOGGER.info("[TAGS][Relance] Application auto du tags fond vert")
    tag = select_tag(tag_type)
    LOGGER.debug(f"[TAGS][{tag.type}] Récupération du tag relance id : {tag.id}")

    stmt_programme_relance = (
        db.select(CodeProgramme.code).where(CodeProgramme.label_theme == "Plan de relance").distinct()
    )
    list_programme = []
    for programme in db.session.execute(stmt_programme_relance).fetchall():
        list_programme.append(programme.code)

    LOGGER.debug(f"[TAGS][{tag.type}] Récupération des programmes appartement au theme Relance")

    apply_task = ApplyTags(tag)
    apply_task.apply_tags_ae(Ae.programme.in_(list_programme))


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

        if db.session.execute(
            stmt_ae
        ).all():  # on vérifie que la liste des lignes à ajouter est non vide. Sinon pas besoin d'insert de nouvelle Assocations
            db.session.execute(
                db.insert(TagAssociation).values(
                    [{"tag_id": self.tag.id, "financial_ae": stmt_ae, "auto_applied": True}]
                )
            )
            db.session.commit()
            LOGGER.info(f"[TAGS][{self.tag.type}] Fin application auto du tags")
        else:
            LOGGER.info(f"[TAGS][{self.tag.type}] Aucune nouvelle association détecté")
