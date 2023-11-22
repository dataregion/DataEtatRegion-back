import logging
from flask_restx import Api, Namespace, SchemaModel
from marshmallow_jsonschema import JSONSchema
from app.models.financial.Ademe import AdemeSchema
from app.models.financial.FinancialAe import FinancialAeSchema
from app.models.financial.FinancialCp import FinancialCpSchema
from app.models.financial.query.FlattenFinancialLines import EnrichedFlattenFinancialLinesSchema
from app.models.tags.Tags import TagsSchema

logger = logging.getLogger(__name__)


def register_tags_schemamodel(api: Api | Namespace) -> SchemaModel:
    """Enregistre le modèle des tags auprès du swagger"""

    tags_schema = TagsSchema()
    tags_model_json = JSONSchema().dump(tags_schema)["definitions"]["TagsSchema"]  # type: ignore
    model_tags_single_api = api.schema_model("TagsSchema", tags_model_json)
    _fix_schemamodel(model_tags_single_api)
    return model_tags_single_api


def register_financial_ae_schemamodel(api: Api | Namespace) -> SchemaModel:
    """Enregistre le modèle FinancialAe auprès du swagger"""

    schema = FinancialAeSchema()
    model_json = JSONSchema().dump(schema)["definitions"]["FinancialAeSchema"]  # type: ignore
    model_single_api = api.schema_model("FinancialAe", model_json)
    _fix_schemamodel(model_single_api)
    return model_single_api


def register_financial_cp_schemamodel(api: Api | Namespace) -> SchemaModel:
    """Enregistre le modèle FinancialAe auprès du swagger"""

    schema = FinancialCpSchema()
    model_json = JSONSchema().dump(schema)["definitions"]["FinancialCpSchema"]  # type: ignore
    model_single_api = api.schema_model("FinancialCp", model_json)
    _fix_schemamodel(model_single_api)
    return model_single_api


def register_flatten_financial_lines_schemamodel(api: Api | Namespace) -> SchemaModel:
    """Enregistre le modèle FlattenBudget auprès du swagger"""

    schema = EnrichedFlattenFinancialLinesSchema()
    model_json = JSONSchema().dump(schema)["definitions"]["EnrichedFlattenFinancialLinesSchema"]  # type: ignore
    model_single_api = api.schema_model("EnrichedFlattenFinancialLinesSchema", model_json)
    _fix_schemamodel(model_single_api)
    return model_single_api


def register_ademe_schemamodel(api: Api | Namespace) -> SchemaModel:
    """Enregistre le modèle Ademe auprès du swagger"""

    schema = AdemeSchema()
    model_json = JSONSchema().dump(schema)["definitions"]["AdemeSchema"]  # type: ignore
    model_single_api = api.schema_model("Ademe", model_json)
    _fix_schemamodel(model_single_api)
    return model_single_api


def _fix_schemamodel(schemaModel: SchemaModel):
    """
    Le schemamodel généré par marshmallow-json n'est pas correct
    Cette fonction corrige si nécessaire.
    """
    _fix_schemamodel_type_with_null(schemaModel)


def _fix_schemamodel_type_with_null(schemaModel: SchemaModel):
    """
    Remplace les 'type': ['type1', 'type2'] par 'type': 'type1'.
    Cela est nécessaire parce que nous avons des 'type': ['type1', 'null']. Ce qui n'est pas correct.
    """

    def _fix(obj: dict):
        for key, value in obj.items():
            if isinstance(value, dict):
                # Si la valeur est un dictionnaire, appeler la fonction de manière récursive
                _fix(value)
            elif key == "type":
                # Si la clé est "type", remplacer la valeur par "string"
                types = obj[key]
                if not isinstance(types, list) or len(types) < 1:
                    continue

                logger.debug(
                    "Trouvé un list de type en tant que proprieté jsonschema 'type'. "
                    " On remplace le tableau de type par le premier type trouvé pour générer un swagger correct."
                )
                first = types[0]
                obj[key] = first

    properties = schemaModel._schema["properties"]
    _fix(properties)
