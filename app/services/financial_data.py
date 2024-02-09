import logging

from app import db

from sqlalchemy import delete

from app.models.financial.FinancialCp import FinancialCp
from app.models.financial.FinancialAe import FinancialAe


def delete_ae(annee: int, source_region: str):
    """
    Supprime AE d'une année comptable d'une région
    :param annee:
    :param source_region:
    :return:
    """
    logging.info(f"[IMPORT FINANCIAL] Suppression des AE pour l'année {annee} et la région {source_region}")
    stmt = delete(FinancialAe).where(FinancialAe.annee == annee).where(FinancialAe.source_region == source_region)
    db.session.execute(stmt)
    db.session.commit()


def delete_cp(annee: int, source_region: str):
    """
    Supprime CP d'une année comptable d'une région
    :param annee:
    :param source_region:
    :return:
    """
    logging.info(f"[IMPORT FINANCIAL] Suppression des CP pour l'année {annee} et la région {source_region}")
    stmt = delete(FinancialCp).where(FinancialCp.annee == annee).where(FinancialCp.source_region == source_region)
    db.session.execute(stmt)
    db.session.commit()
