from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from models.entities.audit.AuditUpdateData import AuditUpdateData


class AuditUpdateDataSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = AuditUpdateData
        exclude = (
            "id",
            "data_type",
        )
