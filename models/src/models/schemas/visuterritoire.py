from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from models.entities.visuterritoire.query.VuesVisuTerritoire import France2030, MontantParNiveauBopAnneeType


class MontantParNiveauBopAnneeTypeSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = MontantParNiveauBopAnneeType


class France2030Schema(SQLAlchemyAutoSchema):
    class Meta:
        model = France2030