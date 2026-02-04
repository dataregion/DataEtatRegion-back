import logging

from app import db

from sqlalchemy import exists, select, delete

from models.entities.financial.FinancialCp import FinancialCp
from models.entities.financial.FinancialAe import FinancialAe


def delete_ae_no_cp_annee_region(annee: int, source_region: str):
    """
    Supprime les AE sans CP d'une année comptable d'une région
    :param annee:
    :param source_region:
    :return:
    """
    logging.info(
        f"[IMPORT FINANCIAL] Suppression des AE n'ayant aucun CP en BDD pour l'année {annee} et la région {source_region}"
    )
    subquery = (select(FinancialCp).where(FinancialCp.id_ae == FinancialAe.id)).exists()
    stmt = (
        delete(FinancialAe)
        .where(~subquery)
        .where(
            FinancialAe.annee == annee, FinancialAe.source_region == source_region, FinancialAe.data_source == "REGION"
        )
    )
    db.session.execute(stmt)
    db.session.commit()


def delete_cp_annee_region(annee: int, source_region: str):
    """
    Supprime CP d'une année comptable d'une région
    La suppression ne se base PAS sur l'année des CP, mais sur l'année des AE auxquelles ils sont liés.

    :param annee: année comptable des AE dont les CP doivent être supprimés
    :param source_region:
    :return:
    """
    logging.info(f"[IMPORT FINANCIAL] Suppression des CP de la région {source_region} liés aux AE de l'année {annee}")
    subquery = exists().where(FinancialCp.id_ae == FinancialAe.id).where(FinancialAe.annee == annee)
    stmt = (
        delete(FinancialCp)
        .where(subquery)
        .where(FinancialCp.source_region == source_region, FinancialCp.data_source == "REGION")
    )
    db.session.execute(stmt)
    db.session.commit()


def delete_ae_no_cp_annee_national(annee: int):
    """
    Supprime les AE sans CP d'une année comptable au niveau national
    :param annee:
    :return:
    """
    logging.info(f"[IMPORT FINANCIAL] Suppression des AE n'ayant aucun CP en BDD pour l'année {annee} du national")
    subquery = (select(FinancialCp).where(FinancialCp.id_ae == FinancialAe.id)).exists()
    stmt = delete(FinancialAe).where(~subquery).where(FinancialAe.annee == annee, FinancialAe.data_source == "NATION")
    db.session.execute(stmt)
    db.session.commit()


def delete_cp_annee_national(annee: int):
    """
    Supprime CP d'une année comptable au niveau National
    La suppression ne se base PAS sur l'année des CP, mais sur l'année des AE auxquelles ils sont liés.

    :param annee: année comptable des AE dont les CP doivent être supprimés
    :return:
    """
    logging.info(f"[IMPORT FINANCIAL] Suppression des CP NATION liés aux AE de l'année {annee}")
    subquery = exists().where(FinancialCp.id_ae == FinancialAe.id).where(FinancialAe.annee == annee)
    stmt = delete(FinancialCp).where(subquery).where(FinancialCp.data_source == "NATION")
    db.session.execute(stmt)
    db.session.commit()
