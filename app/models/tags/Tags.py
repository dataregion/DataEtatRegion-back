from typing import List

from sqlalchemy import CheckConstraint, Column, String, Integer, UniqueConstraint, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship, Mapped

from app import db, ma
from app.models.common.Audit import Audit


class Tags(Audit, db.Model):
    __tablename__ = "tags"
    id = db.Column(Integer, primary_key=True)
    type: str = Column(String(255), unique=True, nullable=False)
    value: str = Column(String(255))
    description: str = Column(Text, nullable=True)
    enable_rules_auto: bool = Column(Boolean, nullable=False, default=False)

    associations: Mapped[List["TagAssociation"]] = relationship(cascade="all, delete", back_populates="tag")
    UniqueConstraint("type", "value", name="unique_tags")


class TagAssociation(Audit, db.Model):
    __tablename__ = "tag_association"
    __table_args__ = (
        CheckConstraint(
            "true", name="line_fks_xor"
        ),  # XXX: voir les scripts de migration our la vraie definition de contrainte
    )

    id = db.Column(Integer, primary_key=True)
    tag_id = Column(Integer, ForeignKey("tags.id"), nullable=False)

    ademe = Column(Integer, ForeignKey("ademe.id"), nullable=True)
    financial_ae = Column(Integer, ForeignKey("financial_ae.id"), nullable=True)

    # indique si le tag a été appliqué par un script auto ou non
    auto_applied = Column(Boolean, default=False, nullable=False)

    tag: Mapped[Tags] = relationship(back_populates="associations")


class TagsSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Tags
        exclude = ("id", "enable_rules_auto",) + Tags.exclude_schema()
