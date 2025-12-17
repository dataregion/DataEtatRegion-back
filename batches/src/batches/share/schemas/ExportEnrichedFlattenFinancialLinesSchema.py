from marshmallow import fields
from models.entities.financial.query.FlattenFinancialLines import EnrichedFlattenFinancialLines
from models.schemas.financial import EnrichedFlattenFinancialLinesSchema
from models.value_objects.tags import TagVO


class ExportEnrichedFlattenFinancialLinesSchema(EnrichedFlattenFinancialLinesSchema):
    """
    Schema spécialisé pour les exports csv de lignes financières
    """

    class Meta:
        model = EnrichedFlattenFinancialLines

    tags = fields.Method("get_tags_csv", dump_only=True)

    def get_tags_csv(self, obj):
        tags_csv = [TagVO(x.type, x.value).fullname for x in obj.tags]
        tags_csv = ",".join(tags_csv)
        return tags_csv
