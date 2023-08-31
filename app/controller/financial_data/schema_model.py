from flask_restx import Api, SchemaModel
from marshmallow_jsonschema import JSONSchema
from app.models.financial.Ademe import AdemeSchema
from app.models.financial.FinancialAe import FinancialAeSchema
from app.models.tags.Tags import TagsSchema


def register_tags_schemamodel(api: Api) -> SchemaModel:
    """Enregistre le modèle des tags auprès du swagger"""

    tags_schema = TagsSchema()
    tags_model_json = JSONSchema().dump(tags_schema)["definitions"]["TagsSchema"]
    model_tags_single_api = api.schema_model("TagsSchema", tags_model_json)
    return model_tags_single_api


def register_financial_ae_schemamodel(api: Api) -> SchemaModel:
    """Enregistre le modèle FinancialAe auprès du swagger"""

    schema = FinancialAeSchema()
    model_json = JSONSchema().dump(schema)["definitions"]["FinancialAeSchema"]
    model_single_api = api.schema_model("FinancialAe", model_json)
    return model_single_api


def register_ademe_schemamodel(api: Api) -> SchemaModel:
    """Enregistre le modèle Ademe auprès du swagger"""

    schema = AdemeSchema()
    model_json = JSONSchema().dump(schema)["definitions"]["AdemeSchema"]
    model_single_api = api.schema_model("Ademe", model_json)
    return model_single_api
