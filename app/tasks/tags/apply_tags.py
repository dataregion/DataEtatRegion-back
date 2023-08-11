import logging

from app import celeryapp

celery = celeryapp.celery
LOGGER = logging.getLogger()


@celery.task(bind=True, name="apply_tags_fond_vert")
def apply_tags_fond_vert(self, tag_type: str):
    """
    Applique les tags Fond Vert
    :param self:
    :param tag_type: le type tag
    :return:
    """

    LOGGER.info("[TAGS][Fond vert] Application auto du tags fond vert")
