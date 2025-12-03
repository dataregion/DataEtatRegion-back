from models import _PersistenceBaseModelInstance
from models.entities.common.Tags import Tags
from models.entities.financial.FinancialData import FinancialData
from sqlalchemy import (
    Boolean,
    Column,
    Date,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship, Mapped

from models.entities.refs.Siret import Siret


from dataclasses import dataclass
from datetime import date, datetime


@dataclass
class Ademe(FinancialData, _PersistenceBaseModelInstance()):
    __tablename__ = "ademe"
    date_convention: Column[date] = Column(Date)

    reference_decision = Column(String(255), nullable=False)

    objet = Column(String(255))
    montant: Column[float] = Column(Float)
    nature = Column(String(255))
    conditions_versement = Column(String(255))
    dates_periode_versement = Column(String(255))
    notification_ue = Column(Boolean, default=False)

    # FK
    siret_attribuant = Column(String, ForeignKey("ref_siret.code"), nullable=True)
    siret_beneficiaire = Column(String, ForeignKey("ref_siret.code"), nullable=True)

    ref_siret_attribuant: Mapped[Siret] = relationship("Siret", lazy="select", foreign_keys=[siret_attribuant])
    ref_siret_beneficiaire: Mapped[Siret] = relationship("Siret", lazy="select", foreign_keys=[siret_beneficiaire])

    tags: Mapped[Tags] = relationship("Tags", uselist=True, lazy="select", secondary="tag_association", viewonly=True)

    # Données techniques
    file_import_taskid = Column(String(255))
    """Task ID de la tâche d'import racine pour cette ligne"""
    file_import_lineno = Column(Integer())
    """Numéro de ligne correspondant dans le fichier original"""

    __table_args__ = (UniqueConstraint("file_import_taskid", "file_import_lineno", name="uq_file_line_import_ademe"),)

    @staticmethod
    def from_datagouv_csv_line(line_dict: dict):
        ademe = Ademe()

        date_convention = line_dict["dateConvention"]
        date_convention = datetime.strptime(date_convention, "%Y-%m-%d").date()

        notification_ue = line_dict["notificationUE"]
        notification_ue = True if notification_ue is not None else False

        ademe.date_convention = date_convention  # type: ignore
        ademe.reference_decision = line_dict["referenceDecision"]
        ademe.objet = line_dict["objet"]
        ademe.montant = line_dict["montant"]
        ademe.nature = line_dict["nature"]
        ademe.conditions_versement = line_dict["conditionsVersement"]
        ademe.dates_periode_versement = line_dict["datesPeriodeVersement"]
        ademe.notification_ue = notification_ue

        ademe.siret_attribuant = line_dict["idAttribuant"]
        ademe.siret_beneficiaire = line_dict["idBeneficiaire"]

        return ademe
