from typing import List

from sqlalchemy import Column, String, Integer, UniqueConstraint, ForeignKey, Boolean, Text
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

    id = db.Column(Integer, primary_key=True)
    tag_id = Column(Integer, ForeignKey("tags.id"), nullable=False)
    association_id = Column(Integer, nullable=False)
    table_association_name = Column(String(255), nullable=False)
    # indique si le tag a été appliqué par un script auto ou non
    auto_applied = Column(Boolean, default=False, nullable=False)

    tag: Mapped[Tags] = relationship(back_populates="associations")
    UniqueConstraint("tag_id", "association_id", "table_association_name", name="unique_association_tags")


class TagsSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Tags
        exclude = ("id",) + Tags.exclude_schema()
