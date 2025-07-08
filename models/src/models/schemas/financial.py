from models.schemas.common import DataTypeField
from marshmallow import fields
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from models.entities.financial.Ademe import Ademe
from models.entities.financial.FinancialAe import FinancialAe
from models.entities.financial.FinancialCp import FinancialCp
from models.entities.financial.query.FlattenFinancialLines import (
    EnrichedFlattenFinancialLines,
)
from models.entities.refs.Siret import Siret
from models.schemas.tags import TagsSchema
from sqlalchemy import String


class EnrichedFlattenFinancialLinesSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = EnrichedFlattenFinancialLines

    source = DataTypeField()

    tags = fields.List(fields.Nested(TagsSchema))


class SiretField(fields.Field):
    """Field Siret"""

    def _jsonschema_type_mapping(self):
        return {
            "type": "object",
            "properties": {
                "nom": {"type": "string"},
                "code": {"type": "string"},
                "categorie_juridique": {"type": "string"},
                "qpv": {"type": "object", "nullable": True},
            },
        }

    def _serialize(self, siret: str, attr: str, obj: Ademe, **kwargs):
        if siret is None:
            return {}
        return {
            "nom_beneficiare": obj.ref_siret_beneficiaire.denomination,
            "code": siret,
            "categorie_juridique": obj.ref_siret_beneficiaire.type_categorie_juridique,
            "qpv": (
                {
                    "code": obj.ref_siret_beneficiaire.ref_qpv.code,
                    "label": obj.ref_siret_beneficiaire.ref_qpv.label,
                }
                if obj.ref_siret_beneficiaire.ref_qpv is not None
                else None
            ),
        }


class CommuneField(fields.Field):
    """Field Commune"""

    def _jsonschema_type_mapping(self):
        return {
            "type": "object",
            "properties": {
                "code": {"type": "string"},
                "label": {"type": "string"},
                "code_region": {"type": "string"},
                "label_region": {"type": "string"},
                "code_departement": {"type": "string"},
                "label_departement": {"type": "string"},
                "code_epci": {"type": "string"},
                "label_epci": {"type": "string"},
                "code_crte": {"type": "string"},
                "label_crte": {"type": "string"},
                "arrondissement": {"type": "object", "nullable": True},
            },
        }

    def _serialize(self, value: Siret, attr, obj, **kwargs):
        if value is None:
            return {}
        return {
            "code": value.ref_commune.code,
            "label": value.ref_commune.label_commune,
            "code_region": value.ref_commune.code_region,
            "label_region": value.ref_commune.label_region,
            "code_departement": value.ref_commune.code_departement,
            "label_departement": value.ref_commune.label_departement,
            "code_epci": value.ref_commune.code_epci,
            "label_epci": value.ref_commune.label_epci,
            "code_crte": value.ref_commune.code_crte,
            "label_crte": value.ref_commune.label_crte,
            "arrondissement": (
                {
                    "code": value.ref_commune.ref_arrondissement.code,
                    "label": value.ref_commune.ref_arrondissement.label,
                }
                if value.ref_commune.ref_arrondissement is not None
                else None
            ),
        }


class AdemeSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Ademe
        exclude = ("updated_at", "created_at", "ref_siret_attribuant")

    tags = fields.List(fields.Nested(TagsSchema))
    siret_beneficiaire = SiretField(attribute="siret_beneficiaire")
    commune = CommuneField(attribute="ref_siret_beneficiaire")


class CommonField(fields.Field):
    def _jsonschema_type_mapping(self):
        """
        Retourne un jsonchema object contenant code et label
        :return:
        """
        return {
            "type": "object",
            "properties": {"label": {"type": "string"}, "code": {"type": "string"}},
        }


class ReferentielField(CommonField):
    """Field Ref programmation"""

    def _serialize(self, code: String, attr, obj: FinancialAe, **kwargs):
        if code is None:
            return {}
        return {"label": obj.ref_ref_programmation.label, "code": code}


class DomaineField(CommonField):
    """Field Domaine fonctionnel"""

    def _serialize(self, code: String, attr, obj: FinancialAe, **kwargs):
        if code is None:
            return {}
        return {"label": obj.ref_domaine_fonctionnel.label, "code": code}


class GroupeMarchandiseField(CommonField):
    """Field Groupe marchandise"""

    def _serialize(self, code: String, attr, obj: FinancialAe, **kwargs):
        if code is None:
            return {}
        return {"label": obj.ref_groupe_marchandise.label, "code": code}


class ProgrammeField(fields.Field):
    """Field programme"""

    def _jsonschema_type_mapping(self):
        return {
            "type": "object",
            "properties": {
                "label": {"type": "string"},
                "code": {"type": "string"},
                "theme": {"type": "string"},
            },
        }

    def _serialize(self, code: String, attr, obj: FinancialAe, **kwargs):
        if code is None:
            return {}
        return {
            "label": obj.ref_programme.label,
            "code": code,
            "theme": obj.ref_programme.label_theme,
        }


class LocalisationInterministerielleField(fields.Field):
    """Field Localisation interministerielle"""

    def _jsonschema_type_mapping(self):
        return {
            "type": "object",
            "properties": {
                "code": {"type": "string"},
                "label": {"type": "string"},
                "commune": {"type": "object", "nullable": True},
            },
        }

    def _serialize(self, code: String, attr, obj: FinancialAe, **kwargs):
        if code is None:
            return {}

        if obj.ref_localisation_interministerielle.commune is None:
            return {
                "code": code,
                "label": obj.ref_localisation_interministerielle.label,
            }

        return {
            "code": code,
            "label": obj.ref_localisation_interministerielle.label,
            "commune": {
                "label": obj.ref_localisation_interministerielle.commune.label_commune,
                "code": obj.ref_localisation_interministerielle.commune.code,
            },
        }


class FinancialAeSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = FinancialAe
        exclude = (
            "updated_at",
            "created_at",
            "source_region",
            "financial_cp",
        )

    TAGS_COLUMNAME = "tags"
    """Nom de la colonne tags"""

    N_EJ_COLUMNAME = "n_ej"
    """Nom de la colonne numéro EJ"""
    N_POSTE_EJ_COLUMNNAME = "n_poste_ej"
    """Nom de la colonne du poste EJ"""

    tags = fields.List(
        fields.Nested(TagsSchema), attribute=TAGS_COLUMNAME, data_key=TAGS_COLUMNAME
    )
    montant_ae = fields.Float(attribute="montant_ae_total")
    montant_cp = fields.Float()
    date_cp = fields.String()
    commune = CommuneField(attribute="ref_siret")
    domaine_fonctionnel = DomaineField(attribute="domaine_fonctionnel")
    referentiel_programmation = ReferentielField()
    groupe_marchandise = GroupeMarchandiseField(attribute="groupe_marchandise")
    localisation_interministerielle = LocalisationInterministerielleField(
        attribute="localisation_interministerielle"
    )
    compte_budgetaire = fields.String()
    contrat_etat_region = fields.String()
    programme = ProgrammeField()
    n_ej = fields.String(attribute=N_EJ_COLUMNAME, data_key=N_EJ_COLUMNAME)
    n_poste_ej = fields.Integer(
        attribute=N_POSTE_EJ_COLUMNNAME, data_key=N_POSTE_EJ_COLUMNNAME
    )
    annee = fields.Integer()
    siret = SiretField()


class FinancialCpSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = FinancialCp
        exclude = (
            "id",
            "id_ae",
            "n_ej",
            "n_poste_ej",
            "annee",
            "compte_budgetaire",
            "contrat_etat_region",
            "date_derniere_operation_dp",
            "file_import_lineno",
            "file_import_taskid",
            "updated_at",
            "created_at",
        )

    n_dp = fields.String()
    montant = fields.Float()
    date_base_dp = fields.String()
