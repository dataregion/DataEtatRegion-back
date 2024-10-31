from marshmallow import fields
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from models.entities.refs.Arrondissement import Arrondissement
from models.entities.refs.CentreCouts import CentreCouts
from models.entities.refs.CodeProgramme import CodeProgramme
from models.entities.refs.Commune import Commune
from models.entities.refs.DomaineFonctionnel import DomaineFonctionnel
from models.entities.refs.GroupeMarchandise import GroupeMarchandise
from models.entities.refs.LocalisationInterministerielle import LocalisationInterministerielle
from models.entities.refs.Ministere import Ministere
from models.entities.refs.Qpv import Qpv
from models.entities.refs.ReferentielProgrammation import ReferentielProgrammation
from models.entities.refs.Siret import Siret
from geoalchemy2.shape import to_shape


class GeometryField(fields.Field):
    def _serialize(self, value, attr, obj, **kwargs):
        # Custom serialization logic for the geometry
        return to_shape(value).wkt if value else None

    def _jsonschema_type_mapping(self):
        # Return a basic string type for JSON schema generation
        return {"type": "string"}

class ArrondissementSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Arrondissement
        exclude = Arrondissement.exclude_schema()


class CentreCoutsSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = CentreCouts
        exclude = ("id",) + CentreCouts.exclude_schema()


class CodeProgrammeSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = CodeProgramme
        include_fk = True
        exclude = (
            "id",
            "theme",
            "theme_r",
        ) + CodeProgramme.exclude_schema()

    label_theme = fields.String()
    label = fields.String()
    code_ministere = fields.String()
    description = fields.String()


class CommuneSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Commune
        exclude = ("id",)

    code = fields.String()
    label_commune = fields.String()


class DomaineFonctionnelSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = DomaineFonctionnel
        exclude = ("id",) + DomaineFonctionnel.exclude_schema()

    code_programme = fields.String()
    label = fields.String()
    description = fields.String()


class GroupeMarchandiseSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = GroupeMarchandise
        exclude = ("id",) + GroupeMarchandise.exclude_schema()

    label = fields.String()
    code = fields.String()
    description = fields.String()
    domaine = fields.String()
    segment = fields.String()
    code_pce = fields.String()
    label_pce = fields.String()


class LocalisationInterministerielleSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = LocalisationInterministerielle
        exclude = (
            "id",
            "commune_id",
        ) + LocalisationInterministerielle.exclude_schema()

    label = fields.String()
    site = fields.String()
    description = fields.String()
    niveau = fields.String()
    code_parent = fields.String()
    commune = fields.Nested(CommuneSchema)


class MinistereSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Ministere
        exclude = Ministere.exclude_schema()


class QpvSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Qpv
        exclude = ("id",) + Qpv.exclude_schema()

    code = fields.String()
    label = fields.String()
    label_commune = fields.String()
    annee_decoupage = fields.Integer()
    geom = GeometryField(dump_only=True)
    centroid = GeometryField(dump_only=True)


class ReferentielProgrammationSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = ReferentielProgrammation
        exclude = ("id",) + ReferentielProgrammation.exclude_schema()

    label = fields.String()
    description = fields.String()
    code_programme = fields.String()


class SiretSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Siret
        exclude = (
            "id",
            "naf",
            "code",
        ) + Siret.exclude_schema()

    siret = fields.String(attribute="code")
    categorie_juridique = fields.String(attribute="type_categorie_juridique")
    denomination = fields.String()
    adresse = fields.String()