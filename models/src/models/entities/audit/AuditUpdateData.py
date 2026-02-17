from datetime import datetime

from models import _PersistenceBaseModelInstance
from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.orm import validates

from models.value_objects.common import DataType


class AuditUpdateData(_PersistenceBaseModelInstance()):
    """
    Table d'audit pour stocker les dernière mise à jours de JDD
    """

    __tablename__ = "audit_update_data"
    __bind_key__ = "audit"
    __table_args__ = {"schema": "audit"}
    # PK
    id: Column[int] = Column(Integer, primary_key=True, nullable=False)

    username: Column[str] = Column(String, nullable=False)
    filename: Column[str] = Column(String, nullable=False)
    data_type: Column[str] = Column(String, nullable=False)
    source_region: Column[str] = Column(String, nullable=True)
    """Type de donnée. Voir `app.models.enums.DataType.DataType`"""

    date: Column[datetime] = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    application_clientid: Column[str] = Column(String, nullable=True)
    """clientid associé à l'outil qui a lancé l'évenement d'import si import manuel"""

    @validates("data_type")
    def validate_data_type(self, _key, data_type):
        if isinstance(data_type, DataType):
            return data_type.value
        return data_type
