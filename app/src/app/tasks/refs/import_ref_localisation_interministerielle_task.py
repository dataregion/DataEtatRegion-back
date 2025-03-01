import codecs

import json
import logging

from sqlalchemy import func

from app import db, celeryapp
from models.entities.refs.Commune import Commune
from models.entities.refs.LocalisationInterministerielle import LocalisationInterministerielle

LOGGER = logging.getLogger()

celery = celeryapp.celery


@celery.task(name="import_line_one_ref_LocalisationInterministerielle")
def import_line_ref_localisation_interministerielle(data: str, **kwargs):
    data = data.replace('\\"', r"'")
    row = json.loads(codecs.decode(data, "unicode_escape"))

    check_loc_inter = LocalisationInterministerielle(
        code=row["code"], label=row["label"], code_parent=row["code_parent"], site=row["site"], niveau=row["niveau"]
    )

    instance = db.session.execute(
        db.select(LocalisationInterministerielle).where(LocalisationInterministerielle.code == check_loc_inter.code)
    ).scalar_one_or_none()

    if check_loc_inter.niveau == "COMMUNE":
        code_commune = check_loc_inter.code[-5:]
        stmt_find_commune = db.select(Commune).where(Commune.code == code_commune)
    else:
        stmt_find_commune = (
            db.select(Commune)
            .where((func.upper(Commune.label_commune) == func.upper(row["commune"])))
            .where(Commune.code_departement == row["code_departement"])
        )
    commune = db.session.execute(stmt_find_commune).scalar_one_or_none()
    if not instance:
        if commune is not None:
            check_loc_inter.commune = commune
        db.session.add(check_loc_inter)
    else:
        instance.label = row["label"]
        instance.code_parent = row["code_parent"]
        instance.site = row["site"]
        instance.niveau = row["niveau"]
        instance.commune = commune

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        LOGGER.exception("[IMPORT][REF] Error sur ajout/maj ref LocalisationInterministerielle dans %s ", row)
        raise e
