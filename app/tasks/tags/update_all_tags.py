import logging

from celery import subtask

from app import celeryapp, db
from app.models.tags.Tags import Tags

celery = celeryapp.celery
LOGGER = logging.getLogger()


@celery.task(bind=True, name="update_all_tags")
def update_all_tags():
    """
    Parcours la liste des tags disponibles et lance leur application auto
    :param self:
    :return:
    """
    LOGGER.info("[TAGS] Start Application des tags")

    stmt = db.select(Tags).where(Tags.enable_rules_auto == True)
    LOGGER.debug("[TAGS] Sélection des tags pour application auto")

    for tag in db.session.execute(stmt).scalars():
        LOGGER.debug(f"[TAGS] {tag.type} {tag.value} tag trouvé pour application auto")
        subtask_name = f"apply_tags_{tag.type}" if tag.value is None else f"apply_tags_{tag.type}_{tag.value}"
        LOGGER.debug(f"[TAGS ]envoi subtask {subtask_name}")
        subtask(subtask_name).delay(tag.type)
    LOGGER.info("[TAGS] End Application des tags")
