from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from models.entities.common.Tags import Tags


class TagsSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Tags
        exclude = (
            "id",
            "enable_rules_auto",
        ) + Tags.exclude_schema()