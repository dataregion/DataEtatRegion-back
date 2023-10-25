import dataclasses
from dataclasses import dataclass
from typing import List

from sqlalchemy import CheckConstraint, Column, String, Integer, UniqueConstraint, ForeignKey, Boolean, Text, func
from sqlalchemy.orm import relationship, Mapped
from sqlalchemy.ext.hybrid import hybrid_property

from app import db, ma
from app.models.common.Audit import Audit


# region: db model
class Tags(Audit, db.Model):
    __tablename__ = "tags"
    id = db.Column(Integer, primary_key=True)
    type: str = Column(String(255), nullable=False)
    value: str = Column(String(255))
    description: str = Column(Text, nullable=True)
    enable_rules_auto: bool = Column(Boolean, nullable=False, default=False)

    associations: Mapped[List["TagAssociation"]] = relationship(cascade="all, delete", back_populates="tag")
    UniqueConstraint("type", "value", name="unique_tags")

    @hybrid_property
    def fullname(self):
        """
        Nom complet du tag, ie. 'type:value' ou 'type:'
        """
        return self.type + ":" + func.coalesce(self.value, "")


@dataclasses.dataclass
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
        exclude = (
            "id",
            "enable_rules_auto",
        ) + Tags.exclude_schema()


# endregion


# region app model
@dataclass
class TagVO:
    """Représente un tag (i.e: un type et une valeur). C'est un value object"""

    type: str
    value: str | None

    @property
    def fullname(self):
        """
        fullname d'un tag correctement formatté pour requête avec la bdd
        voir :meth:`app.models.tags.Tags.fullname`
        """
        type = self.type or ""
        value = self.value or ""
        pretty = f"{type}:{value}"
        return pretty

    @staticmethod
    def from_prettyname(pretty: str):
        """
        Parse un nom de tag
        warning: pretty ne devient pas forcément le fullname du tag
        """
        fullname = _sanitize_tag_prettyname(pretty)
        split = fullname.split(":")
        type = split[0] or None
        value = split[1] or None

        if type is None:
            raise ValueError("Error during parsing tag prettyname. Type should not be empty")

        return TagVO.from_typevalue(type, value)

    @staticmethod
    def from_typevalue(type: str, value: str | None = None):
        return TagVO(type, value)

    @staticmethod
    def sanitize_str(pretty: str):
        """
        Corrige les prettyname des tags pour respecter
        la convention plus stricte de représentation des noms de tags.
        """
        tag = TagVO.from_prettyname(pretty)
        return tag.fullname


def _sanitize_tag_prettyname(pretty_name: str):
    if ":" not in pretty_name:
        return pretty_name + ":"
    return pretty_name


# endregion
