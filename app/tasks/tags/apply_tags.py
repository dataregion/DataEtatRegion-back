import logging

from sqlalchemy import insert

from app import celeryapp, db
from app.models.financial.FinancialAe import FinancialAe as Ae
from app.models.tags.Tags import TagAssociation
from app.tasks.tags import select_ae_have_tags

celery = celeryapp.celery
LOGGER = logging.getLogger()


@celery.task(bind=True, name="apply_tags_fond_vert")
def apply_tags_fond_vert(self, tag_id: int, tag_type: str, tag_value: str | None):
    """
    Applique les tags Fond Vert
    :param self:
    :param tag_id: l'id du tag dans la table du referentiel
    :param tag_type: le nom du type tag
    :param tag_value: la valeur du tag
    :return:
    """

    LOGGER.info("[TAGS][Fond vert] Application auto du tags fond vert")

    LOGGER.info("[TAGS][Fond vert] Select des AE du programme 380 qui n'ont pas de tags")
    stmt = db.select(Ae.id).where(Ae.programme == "380").where(Ae.id.not_in(select_ae_have_tags()))

    db.session.scalars(insert(TagAssociation).values([{"tag_id": tag_id, "financial_ae": stmt, "auto_applied": True}]))
    list_ae = db.session.execute(stmt).all()
