import sys

from flask import current_app
from flask_restx import Namespace, Resource, fields
from flask_restx._http import HTTPStatus
from flask_restx.reqparse import ParseResult
from marshmallow_jsonschema import JSONSchema
from sqlalchemy.exc import NoResultFound

from app import db
from app.controller.utils.ControllerUtils import get_pagination_parser
from app.models.common.Pagination import Pagination


auth = current_app.extensions["auth"]


def build_ref_controller(cls, namespace: Namespace, cond_opt: tuple = None):
    """
    Construit dynamiquement des endpoint pour un referentiel
    L'api contient un endpoint de recherche paginé, et une endpoint pour retourner un objet par son code

    :param cls:   La Classe du modèle. Le schema sera automatiquement détecté si le nom est le même que
    la classe, suffixé par Schema
    :param namespace:  Le namespace du controller
    :param help_query:  Spécification de l'aide pour l'api de recherche
    :param cond_opt:    des Clause supplémentaire pour rechercher des objets. par défaut, on recherche sur le 'code' et le 'label'.
        Exemple pour ajouter un attribut "code_postal" : cond_opt=(CentreCouts.code_postal,)
    :return:
    """
    api = namespace

    module_name = cls().__class__.__module__
    schema = getattr(sys.modules[module_name], f"{cls.__name__}Schema")

    parser_get = get_pagination_parser()
    parser_get.add_argument("code", type=str, required=False, help="Recherche sur le code")
    parser_get.add_argument("label", type=str, required=False, help="Recherche sur le label")
    if cond_opt is not None:
        for cond in cond_opt:
            parser_get.add_argument(
                cond.field.name, type=cond.type, required=cond.required, help=cond.help, action=cond.action
            )

    schema_many = schema(many=True)

    model_json = JSONSchema().dump(schema_many)["definitions"][schema.__name__]
    model_single_api = api.schema_model(cls.__name__, model_json)
    pagination_model = api.schema_model("Pagination", Pagination.definition_jsonschema)

    pagination_with_model = api.model(
        f"{cls.__name__}Pagination",
        {"items": fields.List(fields.Nested(model_single_api)), "pageInfo": fields.Nested(pagination_model)},
    )

    @api.route("")
    @api.doc(model=pagination_with_model)
    class RefControllerList(Resource):
        @auth.token_auth("default", scopes_required=["openid"])
        @api.doc(security="Bearer")
        @api.expect(parser_get)
        @api.response(200, "Success", pagination_with_model)
        @api.response(204, "No Result")
        def get(self):
            args = parser_get.parse_args()
            where_clause = _build_where_clause(cls, args, cond_opt)
            if where_clause is not None:
                stmt = db.select(cls).where(where_clause).order_by(cls.code)
            else:
                stmt = db.select(cls).order_by(cls.code)

            page_result = db.paginate(stmt, per_page=args.get("limit"), page=args.get("page_number"), error_out=False)
            if page_result.items == []:
                return "", HTTPStatus.NO_CONTENT

            result = schema_many.dump(page_result.items)

            return {
                "items": result,
                "pageInfo": Pagination(page_result.total, page_result.page, page_result.per_page).to_json(),
            }, HTTPStatus.OK

    @api.route("/<code>")
    @api.doc(model=model_single_api)
    class RefByCode(Resource):
        @auth.token_auth("default", scopes_required=["openid"])
        @api.doc(security="Bearer")
        @api.response(200, "Success", model_single_api)
        def get(self, code):
            try:
                result = db.session.execute(db.select(cls).filter_by(code=code)).scalar_one()
                schema_m = schema()
                result = schema_m.dump(result)
                return result, HTTPStatus.OK
            except NoResultFound:
                return "", HTTPStatus.NOT_FOUND

    return api


def _build_where_clause(cls, args: ParseResult, cond_opt: tuple):
    """
    Construit dynamiquement la clause where selon les arguments sélectionnés (code, label, + cond_opt)
    :param cls:         L'instance de la clase
    :param args:        Les paramètres de la requête
    :param cond_opt:    Les conditions supplémentaire
    :return:
    """
    where_clause = None
    if args.get("code"):
        where_clause = cls.code.ilike(args.get("code"))

    if args.get("label"):
        where_clause = (
            where_clause | cls.label.ilike(args.get("label"))
            if where_clause is not None
            else cls.label.ilike(args.get("label"))
        )

    if cond_opt is not None:
        for cond in cond_opt:
            if cond.action == "split":
                where_clause = (
                    where_clause | cond.field.in_(args.get(cond.field.name))
                    if where_clause is not None
                    else cond.field.in_(args.get(cond.field.name))
                )
            else:
                where_clause = (
                    where_clause | cond.field.ilike(args.get(cond.field.name))
                    if where_clause is not None
                    else cond.field.ilike(args.get(cond.field.name))
                )

    return where_clause
