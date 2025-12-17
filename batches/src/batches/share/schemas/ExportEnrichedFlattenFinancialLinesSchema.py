from marshmallow import fields
from models.entities.financial.query.FlattenFinancialLines import EnrichedFlattenFinancialLines
from models.schemas.financial import EnrichedFlattenFinancialLinesSchema


class ExportEnrichedFlattenFinancialLinesSchema(EnrichedFlattenFinancialLinesSchema):
    """
    Schema spécialisé pour les exports csv de lignes financières
    """
    class Meta:
        model = EnrichedFlattenFinancialLines

    tags = fields.Method("get_tags_csv", dump_only=True)

    def get_tags_csv(self, obj):
        return ",".join(map(str, obj.tags or []))