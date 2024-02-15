import re
import traceback
from collections import namedtuple
import pandas as pd

import logging
from app import celeryapp
from app.models.financial.FinancialAe import FinancialAeSchema
from app.models.tags.Tags import TagVO
from app.services.tags import ApplyManualTags, select_tags

from sqlalchemy.exc import NoResultFound


_celery = celeryapp.celery
_logger = logging.getLogger(__name__)

__all__ = ("put_tags_to_ae_from_user_export",)

_headers_type = namedtuple("_headers_type", ["n_ej", "poste_ej", "tags"])
PUT_TAGS_CSV_HEADERS = _headers_type(
    n_ej=[FinancialAeSchema.N_EJ_COLUMNAME],
    poste_ej=[
        FinancialAeSchema.N_POSTE_EJ_COLUMNNAME,
        "poste_ej",
    ],  # TODO: à unifier avec l'export csv du frontend (ﾉಥ益ಥ）ﾉ彡┻━┻)
    tags=[FinancialAeSchema.TAGS_COLUMNAME],
)
"""Headers CSV nécessaires pour la commande de put des tags"""
PUT_TAGS_CSV_CHUNKSIZE = 1_000
"""Taille du chunk pour la lecture du fichier de commande de maj de tags"""
PUT_TAGS_CSV_SPLIT_REGEX = r"[|\s]+"
"""Regex utilisé pour split les valeurs de tag"""


@_celery.task(bind=True, name="put_tags_to_ae_from_user_export")
def put_tags_to_ae_from_user_export(self, file: str):
    """
    Applique les tags aux AE depuis un export csv utilisateur.
    Cette tâche n'est pas idempotente et doit être rejouée par l'utilisateur si besoin.
    """

    report = {
        "sent": 0,
        "in-error-before-sending": 0,
        "total": 0,
        "last-traceback": [],
    }

    def process_line(line_dict):
        try:
            n_ej = _get_cell(line_dict, PUT_TAGS_CSV_HEADERS.n_ej)
            poste_ej = _get_cell(line_dict, PUT_TAGS_CSV_HEADERS.poste_ej)
            tags_field = _get_cell(line_dict, PUT_TAGS_CSV_HEADERS.tags)

            if tags_field is None:
                tags = []
            else:
                tags = re.split(PUT_TAGS_CSV_SPLIT_REGEX, tags_field)

            put_tags_to_ae.delay(n_ej, poste_ej, tags)

            _logger.debug(f"Ligne: {n_ej}, {poste_ej} et {tags}")
            report["sent"] += 1
        except Exception as e:
            _logger.warning("Echec lors du traitement de la ligne pour mise à jour de tag", exc_info=e)
            _tb = traceback.format_exception(type(e), e, e.__traceback__)
            report["in-error-before-sending"] += 1
            report["last-traceback"] = _tb

    chunked = pd.read_csv(file, chunksize=PUT_TAGS_CSV_CHUNKSIZE)
    for chunk in chunked:
        df = chunk
        df = df.replace({pd.NA: None})  # XXX: important pour la gestion de valeur vides
        dict_form = df.to_dict(orient="records")

        for line_dict in dict_form:
            process_line(line_dict)
            report["total"] += 1

    return report


@_celery.task(bind=True, name="put_tags_to_ae")
def put_tags_to_ae(self, n_ej: str, poste_ej: str, tags: list[str]):
    _logger.debug(f"Application des tags manuels [ {tags} ] à l'ae ({n_ej, {poste_ej}})")

    tags_vo = [TagVO.from_prettyname(tag) for tag in tags]
    try:
        tags_db = select_tags(tags_vo)
    except NoResultFound as e:
        _logger.exception(f"[PUT_TAGS] Les tags demandés n'existent pas ({tags})", exc_info=e)
        raise

    result = ApplyManualTags(tags_db).put_on_ae(n_ej, poste_ej)
    return result


def _get_cell(line_dict: dict, keys: list[str]):
    """Retrieve a cell of the dict from a list of key synonyms"""
    cell = None
    for key in keys:
        cell = line_dict.get(key, None)
        if cell is not None:
            break
    return cell
