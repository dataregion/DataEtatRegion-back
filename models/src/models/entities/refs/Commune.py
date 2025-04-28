from models import _PersistenceBaseModelInstance
from models.entities.refs.Arrondissement import Arrondissement
from models.entities.refs.QpvCommune import QpvCommune
from models.entities.common.Audit import _Audit
from sqlalchemy import Boolean, Column, Date, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, relationship


from datetime import date


class Commune(_Audit, _PersistenceBaseModelInstance()):
    __tablename__ = "ref_commune"
    id = Column(Integer, primary_key=True)

    code: Column[str] = Column(String, unique=True, nullable=False)
    label_commune: Column[str] = Column(String)

    code_crte: Column[str] = Column(String, nullable=True)
    label_crte: Column[str] = Column(String)

    code_region: Column[str] = Column(String)
    label_region: Column[str] = Column(String)

    code_epci: Column[str] = Column(String)
    label_epci: Column[str] = Column(String)

    code_departement: Column[str] = Column(String)
    label_departement: Column[str] = Column(String)

    is_pvd: Column[bool] = Column(Boolean, nullable=True)
    date_pvd: Column[date] = Column(Date, nullable=True)

    is_acv: Column[bool] = Column(Boolean, nullable=True)
    date_acv: Column[date] = Column(Date, nullable=True)

    # FK
    code_arrondissement: Column[str] = Column(
        String, ForeignKey("ref_arrondissement.code"), nullable=True
    )
    ref_arrondissement: Mapped[Arrondissement] = relationship(
        "Arrondissement", lazy="joined"
    )
    
    qpvs = relationship("Qpv", secondary=QpvCommune.__table__, backref="qpv_communes", viewonly=True)
