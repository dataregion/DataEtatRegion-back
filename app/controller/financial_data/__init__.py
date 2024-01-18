from functools import wraps

from flask import Blueprint, request
from flask_restx import Api, reqparse, inputs
from flask_restx._http import HTTPStatus
from werkzeug.datastructures import FileStorage
from app.controller.financial_data.schema_model import (
    register_tags_schemamodel,
)

from app.controller.utils.Error import ErrorController
from app.exceptions.exceptions import DataRegatException, BadRequestDataRegateNum


parser_import = reqparse.RequestParser()
parser_import.add_argument("fichier", type=FileStorage, help="fichier à importer", location="files", required=True)
parser_import.add_argument(
    "annee", type=int, help="Année d'engagement du fichier Chorus", location="files", required=True
)
parser_import.add_argument(
    "code_region", type=str, help="Code de la region concerné par l'import", location="files", required=True
)
parser_import.add_argument(
    "force_update",
    type=inputs.boolean,
    required=False,
    default=False,
    location="files",
    help="Force la mise à jours si la ligne existe déjà",
)


def check_param_source_annee_import():
    """
    Vérifie sur la request contient les paramètres code_region et annee
    :return:
    """

    def wrapper(func):
        @wraps(func)
        def inner_wrapper(*args, **kwargs):
            data = request.form
            if "code_region" not in data or "annee" not in data:
                raise BadRequestDataRegateNum("Missing Argument code_region or annee")
            if not isinstance(int(data["annee"]), int):
                raise BadRequestDataRegateNum("Missing Argument code_region or annee")
            return func(*args, **kwargs)

        return inner_wrapper

    return wrapper


def check_file_import():
    """
    Vérifie sur la request contient un attribut fichier
    :return:
    """

    def wrapper(func):
        @wraps(func)
        def inner_wrapper(*args, **kwargs):
            if "fichier" not in request.files:
                raise BadRequestDataRegateNum("Missing File")
            return func(*args, **kwargs)

        return inner_wrapper

    return wrapper


from app.controller.financial_data.FinancialAeCtrl import api as api_ae  # noqa: E402
from app.controller.financial_data.FinancialCpCtrl import api as api_cp  # noqa: E402
from app.controller.financial_data.AdemeCtrl import api as api_ademe  # noqa: E402
from app.controller.financial_data.TagsCtrl import api as api_tags  # noqa: E402
from app.controller.utils.LoginController import api as api_auth  # noqa: E402

from app.controller.financial_data.v2 import api_ns as api_ae_v2  # noqa: E402


api_financial_v1 = Blueprint("financial_data", __name__)
api_financial_v2 = Blueprint("financial_data_v2", __name__)

authorizations = {"Bearer": {"type": "apiKey", "in": "header", "name": "Authorization"}}

_description = (
    "API de gestion des données financière"
    "<br />"
    "<strong>C'est une API dediée à l'outil interne de consultation budget. "
    "N'utilisez pas cette API pour intégrer nos données à votre système.</strong>"
)
api_v1 = Api(
    api_financial_v1,
    doc="/doc",
    prefix="/api/v1",
    description=_description,
    title="API Data transform",
    authorizations=authorizations,
)

model_tags_single_api = register_tags_schemamodel(api_v1)


api_v1.add_namespace(api_auth)
api_v1.add_namespace(api_tags)
api_v1.add_namespace(api_ae)
api_v1.add_namespace(api_cp)
api_v1.add_namespace(api_ademe)

_description = (
    "Api de d'accès aux données financières de l'état "
    "<br />"
    "<strong>C'est une API dediée à l'outil interne de consultation budget. "
    "utilisez pas cette API pour intégrer nos données à votre système.</strong>"
)
api_v2 = Api(
    api_financial_v2,
    version="2.0",
    doc="/api/v2/doc",
    prefix="/api/v2",
    description=_description,
    title="API Data transform",
    authorizations=authorizations,
)

model_tags_single_api = register_tags_schemamodel(api_v2)

api_v2.add_namespace(api_ae_v2)


@api_financial_v1.errorhandler(DataRegatException)
def handle_exception(e):
    return ErrorController(e.message).to_json(), HTTPStatus.BAD_REQUEST


@api_financial_v2.errorhandler(DataRegatException)
def handle_exception_for_api_v2(e):
    return ErrorController(e.message).to_json(), HTTPStatus.BAD_REQUEST
