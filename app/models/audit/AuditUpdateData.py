import datetime
import enum

from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.orm import validates

from app import db, ma
from app.models.enums.DataType import DataType


class AuditUpdateData(db.Model):
    """
    Table d'audit pour stocker les dernière mise à jours de JDD
    """

    __tablename__ = "audit_update_data"
    __bind_key__ = "audit"
    # PK
    id: int = Column(Integer, primary_key=True, nullable=False)

    username: str = Column(String, nullable=False)
    filename: str = Column(String, nullable=False)
    data_type: DataType = Column(String, nullable=False)

    date: DateTime = Column(DateTime(timezone=True), default=datetime.datetime.utcnow, nullable=False)

    @validates("data_type")
    def validate_data_type(self, _key, data_type):
        if isinstance(data_type, DataType):
            return data_type.value
        return data_type


class AuditUpdateDataSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = AuditUpdateData
        exclude = (
            "id",
            "data_type",
        )
