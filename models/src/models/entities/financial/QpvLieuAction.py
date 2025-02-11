from dataclasses import dataclass
from models import _PersistenceBaseModelInstance
from models.entities.common.Audit import _Audit
from models.entities.financial.FinancialAe import FinancialAe
from psycopg import IntegrityError
from sqlalchemy import Column, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.event import listens_for
from sqlalchemy.orm import relationship

import logging

from app.database import db


@dataclass
class QpvLieuAction(_Audit, _PersistenceBaseModelInstance()):
    __tablename__ = "qpv_lieu_action"
    __table_args__ = (UniqueConstraint('code_qpv', 'n_ej', name='uq_qpv_ej'),)

    id = Column(Integer, primary_key=True)
    code_reference = Column(String, nullable=False)
    code_qpv = Column(String, ForeignKey("ref_qpv.code"), nullable=False)
    n_ej: Column[str] = Column(String, nullable=False)
    annee = Column(Integer, nullable=False, autoincrement=False)
    ratio_montant = Column(Float(decimal_return_scale=2), nullable=False, autoincrement=False)

    # Données techniques
    file_import_taskid = Column(String(255))
    file_import_lineno = Column(Integer())

    ref_qpv = relationship("Qpv", foreign_keys=[code_qpv], lazy="joined")

    @staticmethod
    def format_dict(line_dict: dict):
        dict = {}
        dict["code_qpv"] = line_dict["code_qpv"]
        dict["code_reference"] = line_dict["reference"]
        dict["n_ej"] = line_dict["ej"]
        dict["annee"] = int(line_dict["annee"])
        dict["ratio_montant"] = line_dict["ratio_montant_ej"]
        return dict
    

@listens_for(QpvLieuAction, "before_insert")
@listens_for(QpvLieuAction, "before_update")
def check_ej_exists(mapper, connection, target: QpvLieuAction):
    print("print COUCOUCOU")
    logging.debug("logging COUCOUCOU")
    if db.session.query(FinancialAe).filter_by(n_ej=target.n_ej).count() == 0:
        raise IntegrityError(f"N°EJ {target.n_ej} does not exist.", target, [])
        # print(f"N°EJ {target.n_ej} does not exist.")
