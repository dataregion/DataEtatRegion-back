import json
import logging
import string

from celery import subtask

from app import celeryapp, db
from models.entities.common.Tags import Tags

celery = celeryapp.celery
LOGGER = logging.getLogger()

__all__ = (
    "update_all_tags",
    "update_all_tags_of_ae",
    "update_all_tags_of_cp",
)


@celery.task(bind=True, name="update_all_tags")
def update_all_tags(self):
    """
    Parcours la liste des tags disponibles et lance leur application auto
    :param self:
    :return:
    """
    LOGGER.info("[TAGS] Start Application des tags")

    stmt = db.select(Tags).where(Tags.enable_rules_auto == True)  # noqa: E712
    LOGGER.debug("[TAGS] Sélection des tags pour application auto")

    translator = str.maketrans(string.whitespace + "-", "_" * len(string.whitespace + "-"))

    for tag in db.session.execute(stmt).scalars():
        LOGGER.debug(f"[TAGS] {tag.type} {tag.value} tag trouvé pour application auto")
        type = tag.type.lower().translate(translator)
        value = tag.value.lower().translate(translator) if tag.value is not None else None
        subtask_name = f"apply_tags_{type}" if value is None else f"apply_tags_{type}_{value}"
        LOGGER.debug(f"[TAGS ]envoi subtask {subtask_name}")
        subtask(subtask_name).delay(tag.type, tag.value, None)

    LOGGER.info("[TAGS] End Application des tags")


@celery.task(bind=True, name="update_all_tags_of_ae")
def update_all_tags_of_ae(self, id_ae: int):
    """
    Parcours la liste des tags disponibles et lance leur application auto
    :param self:
    :return:
    """
    LOGGER.info(f"[TAGS] Start - Application des tags pour l'AE {id_ae}")

    stmt = db.select(Tags).where(Tags.enable_rules_auto == True)  # noqa: E712
    LOGGER.debug("[TAGS] Sélection des tags pour application auto")

    translator = str.maketrans(string.whitespace + "-", "_" * len(string.whitespace + "-"))

    for tag in db.session.execute(stmt).scalars():
        LOGGER.debug(f"[TAGS] {tag.type} {tag.value} tag trouvé pour application auto")
        type = tag.type.lower().translate(translator)
        value = tag.value.lower().translate(translator) if tag.value is not None else None
        subtask_name = f"apply_tags_{type}" if value is None else f"apply_tags_{type}_{value}"
        LOGGER.debug(f"[TAGS ] envoi subtask {subtask_name}")
        subtask(subtask_name).delay(tag.type, tag.value, json.dumps({"only": "FINANCIAL_DATA_AE", "id": id_ae}))

    LOGGER.info(f"[TAGS] End - Application des tags pour l'AE {id_ae}")


@celery.task(bind=True, name="update_all_tags_of_cp")
def update_all_tags_of_cp(self, id_cp: int):
    """
    Parcours la liste des tags disponibles et lance leur application auto
    :param self:
    :return:
    """
    LOGGER.info(f"[TAGS] Start - Application des tags pour le CP {id_cp}")

    stmt = db.select(Tags).where(Tags.enable_rules_auto == True)  # noqa: E712
    LOGGER.debug("[TAGS] Sélection des tags pour application auto")

    translator = str.maketrans(string.whitespace + "-", "_" * len(string.whitespace + "-"))

    for tag in db.session.execute(stmt).scalars():
        LOGGER.debug(f"[TAGS] {tag.type} {tag.value} tag trouvé pour application auto")
        type = tag.type.lower().translate(translator)
        value = tag.value.lower().translate(translator) if tag.value is not None else None
        subtask_name = f"apply_tags_{type}" if value is None else f"apply_tags_{type}_{value}"
        LOGGER.debug(f"[TAGS ] envoi subtask {subtask_name}")
        subtask(subtask_name).delay(tag.type, tag.value, json.dumps({"only": "FINANCIAL_DATA_CP", "id": id_cp}))

    LOGGER.info(f"[TAGS] End - Application des tags pour le CP {id_cp}")
