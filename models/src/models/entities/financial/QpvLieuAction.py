from dataclasses import dataclass
from models import _PersistenceBaseModelInstance
from models.entities.common.Audit import _Audit
from sqlalchemy import Column, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship


@dataclass
class QpvLieuAction(_Audit, _PersistenceBaseModelInstance()):
    __tablename__ = "qpv_lieu_action"
    __table_args__ = (
        UniqueConstraint(
            "annee_exercice",
            "ref_action",
            "ej",
            "code_qpv",
            name="uq_qpv_lieu_action_metier",
        ),
    )

    id = Column(Integer, primary_key=True)
    annee_exercice: Column[int] = Column(Integer, nullable=False, autoincrement=False)
    ref_action: Column[str] = Column(String, nullable=False)
    ej: Column[str] = Column(String, nullable=False)
    code_qpv: Column[str] = Column(String, ForeignKey("ref_qpv.code"), nullable=False)
    montant_ventille: Column[float] = Column(Float(decimal_return_scale=2), nullable=False, autoincrement=False)
    libelle_action: Column[str] = Column(String, nullable=False)
    siret: Column[str] = Column(String, nullable=False)

    # Données techniques
    file_import_taskid = Column(String(255))
    file_import_lineno = Column(Integer())

    ref_qpv = relationship("Qpv", foreign_keys=[code_qpv], lazy="joined")

    @staticmethod
    def format_dict(line_dict: dict):
        dict = {}
        dict["code_qpv"] = line_dict["code_qpv"]
        dict["ref_action"] = line_dict["ref_action"]
        dict["ej"] = line_dict["ej"]
        dict["annee_exercice"] = int(line_dict["annee_exercice"])
        dict["montant_ventille"] = line_dict["montant_ventillé"]
        dict["libelle_action"] = line_dict["libellé action"]
        dict["siret"] = line_dict["siret"]
        return dict
