import json
import logging
from typing import NamedTuple

from sqlalchemy import ColumnElement

from app import celeryapp, db
from app.models.enums.DataType import DataType
from app.models.financial.FinancialAe import FinancialAe as Ae
from app.models.financial.FinancialCp import FinancialCp as Cp
from app.models.refs.commune import Commune
from app.models.refs.siret import Siret
from app.models.refs.localisation_interministerielle import LocalisationInterministerielle
from app.services.tags import select_tag, ApplyTagForAutomation, TagVO
from app.models.refs.code_programme import CodeProgramme
from app.models.refs.referentiel_programmation import ReferentielProgrammation

_celery = celeryapp.celery
_logger = logging.getLogger()


__all__ = ("apply_tags_fonds_vert", "apply_tags_relance", "apply_tags_detr", "apply_tags_cper_2015_20")


class ContextApplyTags(NamedTuple):
    only: DataType
    id: int | None


@_celery.task(bind=True, name="apply_tags_fonds_vert")
def apply_tags_fonds_vert(self, tag_type: str, _tag_value: str | None, context: dict | None):
    """
    Applique les tags Fond Vert
    :param self:
    :param tag_type: le nom du type tag
    :param _tag_value: la valeur du tag
    :param context:
    :return:
    """
    context = ContextApplyTags(**json.loads(context)) if context is not None else None
    if context is not None and DataType(context.only) != DataType.FINANCIAL_DATA_AE:
        return

    _logger.info("[TAGS][Fond vert] Application auto du tags fond vert")
    tag = select_tag(TagVO.from_typevalue(tag_type))
    _logger.debug(f"[TAGS][Fond vert] Récupération du tag fond vert id : {tag.id}")

    condition = Ae.programme == "380"
    if context is not None and DataType(context.only) is DataType.FINANCIAL_DATA_AE and context.id is not None:
        condition &= Ae.id == context.id

    apply_task = ApplyTagForAutomation(tag)
    apply_task.apply_tags_ae(condition)


@_celery.task(bind=True, name="apply_tags_relance")
def apply_tags_relance(self, tag_type: str, _tag_value: str | None, context: str | None):
    """
    Applique les tags Fond Vert
    :param self:
    :param tag_type: le nom du type tag
    :param _tag_value: la valeur du tag
    :param context:
    :return:
    """
    context = ContextApplyTags(**json.loads(context)) if context is not None else None
    if context is not None and DataType(context.only) is not DataType.FINANCIAL_DATA_AE:
        return

    _logger.info("[TAGS][Relance] Application auto du tags relance")
    tag = select_tag(TagVO.from_typevalue(tag_type))
    _logger.debug(f"[TAGS][{tag.type}] Récupération du tag relance id : {tag.id}")

    stmt_programme_relance = (
        db.select(CodeProgramme.code).where(CodeProgramme.label_theme == "Plan de relance").distinct()
    )
    list_programme = []
    for programme in db.session.execute(stmt_programme_relance).fetchall():
        list_programme.append(programme.code)
    _logger.debug(f"[TAGS][{tag.type}] Récupération des programmes appartement au theme Relance")

    condition = Ae.programme.in_(list_programme)
    if context is not None and DataType(context.only) is DataType.FINANCIAL_DATA_AE and context.id is not None:
        condition &= Ae.id == context.id

    apply_task = ApplyTagForAutomation(tag)
    apply_task.apply_tags_ae(condition)


@_celery.task(bind=True, name="apply_tags_detr")
def apply_tags_detr(self, tag_type: str, _tag_value: str | None, context: str | None):
    """
    Applique le tag DETR
    :param self:
    :param tag_type: le nom du type tag
    :param _tag_value: la valeur du tag
    :param context:
    :return:
    """
    context = ContextApplyTags(**json.loads(context)) if context is not None else None
    if context is not None and DataType(context.only) is not DataType.FINANCIAL_DATA_AE:
        return

    _logger.info("[TAGS][DETR] Application auto du tags DETR")
    tag = select_tag(TagVO.from_typevalue(tag_type))
    _logger.debug(f"[TAGS][{tag.type}] Récupération du tag DETR id : {tag.id}")

    stmt_ref_programmation = (
        db.select(ReferentielProgrammation.code).where(ReferentielProgrammation.label.ilike("detr")).distinct()
    )
    list_ref_programmation = []
    for ref_progammation in db.session.execute(stmt_ref_programmation).fetchall():
        list_ref_programmation.append(ref_progammation.code)

    condition = Ae.referentiel_programmation.in_(list_ref_programmation)
    _logger.debug(f"[TAGS][{tag.type}] Récupération des ref programmation DETR")
    if context is not None and DataType(context.only) is DataType.FINANCIAL_DATA_AE and context.id is not None:
        condition &= Ae.id == context.id

    apply_task = ApplyTagForAutomation(tag)
    apply_task.apply_tags_ae(condition)


@_celery.task(bind=True, name="apply_tags_cper_2015_20")
def apply_tags_cper_2015_20(self, tag_type: str, tag_value: str | None, context: str | None):
    """
    Applique le tag CEPR (Contrat plan Etat Region) entre 2015 et 2020
    :param self:
    :param tag_type:
    :param tag_value:
    :param context:
    :return:
    """
    context = ContextApplyTags(**json.loads(context)) if context is not None else None
    if context is not None and DataType(context.only) is not DataType.FINANCIAL_DATA_AE:
        return

    _logger.info("[TAGS][CPER] Application auto du tags CPER 2015-20")
    tag = select_tag(TagVO.from_typevalue(tag_type, tag_value))
    _logger.debug(f"[TAGS][{tag.type}] Récupération du tag CPER id : {tag.id}")

    condition = (Ae.contrat_etat_region != "#") & (Ae.annee >= 2015) & (Ae.annee <= 2020)
    if context is not None and DataType(context.only) is DataType.FINANCIAL_DATA_AE and context.id is not None:
        condition &= Ae.id == context.id

    apply_task = ApplyTagForAutomation(tag)
    apply_task.apply_tags_ae(condition)


@_celery.task(bind=True, name="apply_tags_cepr_2021_27")
def apply_tags_cepr_2021_27(self, tag_type: str, tag_value: str | None, context: str | None):
    """
    Applique le tag CEPR (Contrat plan Etat Region) entre 2021 et 2027
    :param self:
    :param tag_type:
    :param tag_value:
    :param context:
    :return:
    """
    context = ContextApplyTags(**json.loads(context)) if context is not None else None
    if context is not None and DataType(context.only) is not DataType.FINANCIAL_DATA_AE:
        return

    _logger.info("[TAGS][CPER] Application auto du tags CPER 2021-27")
    tag = select_tag(TagVO.from_typevalue(tag_type, tag_value))
    _logger.debug(f"[TAGS][{tag.type}] Récupération du tag CPER id : {tag.id}")

    condition = (Ae.contrat_etat_region != "#") & (Ae.annee >= 2021) & (Ae.annee <= 2027)
    if context is not None and DataType(context.only) is DataType.FINANCIAL_DATA_AE and context.id is not None:
        condition &= Ae.id == context.id

    apply_task = ApplyTagForAutomation(tag)
    apply_task.apply_tags_ae(condition)


@_celery.task(bind=True, name="apply_tags_pvd")
def apply_tags_pvd(self, tag_type: str, tag_value: str | None, context: str | None):
    """
    Applique le tag PVD (Petite Ville de Demain)
    :param self:
    :param tag_type:
    :param tag_value:
    :param context:
    :return:
    """
    context = ContextApplyTags(**json.loads(context)) if context is not None else None
    if context is not None and DataType(context.only) is not DataType.FINANCIAL_DATA_AE:
        return

    _logger.info("[TAGS][PVD] Application auto du tags PVD")
    tag = select_tag(TagVO.from_typevalue(tag_type))
    _logger.debug(f"[TAGS][{tag.type}] Récupération du tag PVD id : {tag.id}")

    # Récupération des codes des communes PVD
    stmt_communes_pvd = db.select(Commune.id, Commune.code).where(Commune.is_pvd == True)  # noqa: E712
    communes_pvd = db.session.execute(stmt_communes_pvd).fetchall()
    _logger.debug(f"[TAGS][{tag.type}] Récupération des communes PVD")

    # Création des conditions
    siret_condition: ColumnElement[bool] = Ae.ref_siret.has(Siret.code_commune.in_([c.code for c in communes_pvd]))
    loc_condition: ColumnElement[bool] = Ae.ref_localisation_interministerielle.has(
        LocalisationInterministerielle.commune_id.in_([c.id for c in communes_pvd])
    )

    condition = siret_condition | loc_condition
    if context is not None and DataType(context.only) is DataType.FINANCIAL_DATA_AE and context.id is not None:
        condition &= Ae.id == context.id

    # Application du tag aux AE
    apply_task = ApplyTagForAutomation(tag)
    apply_task.apply_tags_ae(condition)


@_celery.task(bind=True, name="apply_tags_cp_orphelin")
def apply_tags_cp_orphelin(self, tag_type: str, tag_value: str | None, context: str | None):
    """
    Applique le tag CP Orphelin sur un CP sans AE
    :param self:
    :param tag_type:
    :param tag_value:
    :param context:
    :return:
    """
    context = ContextApplyTags(**json.loads(context)) if context is not None else None
    if context is not None and DataType(context.only) is not DataType.FINANCIAL_DATA_CP:
        return

    _logger.info("[TAGS][cp-orphelin] Application auto du tags CP Orphelin")
    tag = select_tag(TagVO.from_typevalue(tag_type))
    _logger.debug(f"[TAGS][{tag.type}] Récupération du tag CP ORPHELIN id : {tag.id}")

    condition = Cp.id_ae == None  # noqa: E711
    if context is not None and DataType(context.only) is DataType.FINANCIAL_DATA_CP and context.id is not None:
        condition &= Cp.id == context.id

    # Application du tag aux entités
    apply_task = ApplyTagForAutomation(tag)
    apply_task.apply_tags_cp(condition)


@_celery.task(bind=True, name="apply_tags_acv")
def apply_tags_acv(self, tag_type: str, tag_value: str | None, context: str | None):
    """
    Applique le tag ACV (Action Coeur de la Ville)
    :param self:
    :param tag_type:
    :param tag_value:
    :param context:
    :return:
    """
    context = ContextApplyTags(**json.loads(context)) if context is not None else None
    if context is not None and DataType(context.only) is not DataType.FINANCIAL_DATA_AE:
        return

    _logger.info("[TAGS][ACV] Application auto du tags ACV")
    tag = select_tag(TagVO.from_typevalue(tag_type))
    _logger.debug(f"[TAGS][{tag.type}] Récupération du tag ACV id : {tag.id}")

    # Récupération des codes des communes ACV
    stmt_communes_acv = db.select(Commune.id, Commune.code).where(Commune.is_acv == True)  # noqa: E712
    communes_acv = db.session.execute(stmt_communes_acv).fetchall()
    _logger.debug(f"[TAGS][{tag.type}] Récupération des communes ACV")

    # Création des conditions
    siret_condition: ColumnElement[bool] = Ae.ref_siret.has(Siret.code_commune.in_([c.code for c in communes_acv]))
    loc_condition: ColumnElement[bool] = Ae.ref_localisation_interministerielle.has(
        LocalisationInterministerielle.commune_id.in_([c.id for c in communes_acv])
    )

    condition = siret_condition | loc_condition
    if context is not None and DataType(context.only) is DataType.FINANCIAL_DATA_AE and context.id is not None:
        condition &= Ae.id == context.id

    # Application du tag aux AE
    apply_task = ApplyTagForAutomation(tag)
    apply_task.apply_tags_ae(condition)
