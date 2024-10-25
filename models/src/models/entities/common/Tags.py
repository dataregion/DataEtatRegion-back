import dataclasses
from models import _PersistenceBaseModelInstance
from models.entities.common.Audit import _Audit
from sqlalchemy import Boolean, CheckConstraint, Column, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, relationship


from typing import List

class Tags(_Audit, _PersistenceBaseModelInstance()):
    __tablename__ = "tags"
    __table_args__ = (UniqueConstraint("type", "value", name="uq_type_value_tags"),)
    id = Column(Integer, primary_key=True)
    type: Column[str] = Column(String(255), nullable=False)
    value: Column[str] = Column(String(255))
    description: Column[str] = Column(Text, nullable=True)
    display_name: Column[str] = Column(String(255), nullable=False)
    """Nom du tag destiné à l'affichage UI"""
    enable_rules_auto: Column[bool] = Column(Boolean, nullable=False, default=False)

    associations: Mapped[List["TagAssociation"]] = relationship(cascade="all, delete", back_populates="tag")

    @hybrid_property
    def fullname(self):
        """
        Nom complet du tag, ie. 'type:value' ou 'type:'
        """
        return self.type + ":" + func.coalesce(self.value, "")


@dataclasses.dataclass
class TagAssociation(_Audit, _PersistenceBaseModelInstance()):
    __tablename__ = "tag_association"
    __table_args__ = (
        CheckConstraint(
            "true", name="line_fks_xor"
        ),  # XXX: voir les scripts de migration our la vraie definition de contrainte
    )

    id = Column(Integer, primary_key=True)
    tag_id = Column(Integer, ForeignKey("tags.id", ondelete="cascade"), nullable=False)

    ademe = Column(Integer, ForeignKey("ademe.id", ondelete="cascade"), nullable=True, index=True)
    financial_ae = Column(Integer, ForeignKey("financial_ae.id", ondelete="cascade"), nullable=True, index=True)
    financial_cp = Column(Integer, ForeignKey("financial_cp.id", ondelete="cascade"), nullable=True, index=True)

    # indique si le tag a été appliqué par un script auto ou non
    auto_applied = Column(Boolean, default=False, nullable=False)

    tag: Mapped[Tags] = relationship(back_populates="associations")



