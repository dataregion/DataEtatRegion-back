from marshmallow import fields
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema

from models.entities.demarches.Demarche import Demarche
from models.entities.demarches.Donnee import Donnee
from models.entities.demarches.Dossier import Dossier
from models.entities.demarches.Reconciliation import Reconciliation
from models.entities.demarches.Section import Section
from models.entities.demarches.Token import Token
from models.entities.demarches.Type import Type
from models.entities.demarches.ValeurDonnee import ValeurDonnee


class TokenSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Token
        exclude = ('_token',)
    token = fields.String()

class DemarcheSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Demarche

class DonneeSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Donnee
        exclude = ("demarche",)

class DossierSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Dossier


class ReconciliationSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Reconciliation


class SectionSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Section


class TypeSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Type


class ValeurDonneeSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = ValeurDonnee
        exclude = ("additional_data",)

    dossier_number = fields.Integer()
    donnee_id = fields.Integer()
    valeur = fields.String()
    donnee = fields.Nested(DonneeSchema)
