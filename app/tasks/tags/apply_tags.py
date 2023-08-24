import logging

from app import celeryapp, db
from app.models.financial.FinancialAe import FinancialAe as Ae
from app.models.tags.Tags import TagAssociation
from . import select_ae_have_tags, select_tag

celery = celeryapp.celery
LOGGER = logging.getLogger()


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

    LOGGER.info("[TAGS][Fond vert] Select des AE du programme 380 qui n'ont pas le tags")
    stmt = db.select(Ae.id).where(Ae.programme == "380").where(Ae.id.not_in(select_ae_have_tags(tag.id)))

    if db.session.execute(stmt).all(): # on vérifie que la liste des lignes à ajouter est non vide. Sinon pas besoin d'insert de nouvelle Assocations
        db.session.execute(
            db.insert(TagAssociation).values([{"tag_id": tag.id, "financial_ae": stmt, "auto_applied": True}])
        )
        db.session.commit()
        LOGGER.info("[TAGS][Fond vert] Fin application auto du tags fond vert")
    else :
        LOGGER.info("[TAGS][Fond vert] Aucun nouveau fond vert détecté")


