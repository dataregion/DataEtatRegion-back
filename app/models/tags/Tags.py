from sqlalchemy import Column, String, Integer, UniqueConstraint

from app import db, ma
from app.models.common.Audit import Audit


class Tags(Audit, db.Model):
    __tablename__ = "tags"
    id = db.Column(Integer, primary_key=True)
    type: str = Column(String, unique=True, nullable=False)
    value: str = Column(String(255))

    UniqueConstraint("type", "value", name="unique_tags")


class TagsSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Tags
        exclude = ("id",) + Tags.exclude_schema()
