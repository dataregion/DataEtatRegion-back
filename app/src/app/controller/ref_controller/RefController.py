from flask import current_app
from flask_restx import Namespace, Resource, fields
from flask_restx._http import HTTPStatus
from flask_restx.reqparse import ParseResult
from marshmallow import Schema
from marshmallow_jsonschema import JSONSchema
from sqlalchemy.exc import NoResultFound

from app import db
from app.controller.utils.ControllerUtils import get_pagination_parser
from app.models.common.Pagination import Pagination

from sqlalchemy import and_, or_


auth = current_app.extensions["auth"]


def build_ref_controller(cls, schema_cls: type[Schema], namespace: Namespace, cond_opt: tuple = None):
    """
    Construit dynamiquement des endpoint pour un referentiel
    L'api contient un endpoint de recherche paginé, et une endpoint pour retourner un objet par son code

    :param cls:   La Classe du modèle.
    :param schema_cls: La classe du schema
    :param namespace:  Le namespace du controller
    :param help_query:  Spécification de l'aide pour l'api de recherche
    :param cond_opt:    des Clause supplémentaire pour rechercher des objets. par défaut, on recherche sur le 'code' et le 'label'.
        Exemple pour ajouter un attribut "code_postal" : cond_opt=(CentreCouts.code_postal,)
    :return:
    """
    api = namespace

    schema = schema_cls

    parser_get = get_pagination_parser()
    parser_get.add_argument("query", type=str, required=False, help="Recherche sur le code ou le label")
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
        @auth("openid")
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
        @auth("openid")
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
    # Retour de None si aucun paramètre (uniquement page_number et limit)
    args_no_none = [t for t in list(args.items()) if None not in t]
    if len(args_no_none) == 2:
        return None

    # Condition sur code OR label
    code_label_clause = and_(True)
    if args.get("query"):
        if hasattr(cls, "code"):
            code_label_clause = and_(code_label_clause, cls.code.ilike(f"%{args.get('query')}%"))
        if hasattr(cls, "label"):
            code_label_clause = or_(code_label_clause, cls.label.ilike(f"%{args.get('query')}%"))

    # Conditions particulières
    conditions_clause = []
    if cond_opt is not None:
        for cond in cond_opt:
            if args.get(cond.field.name):
                if cond.action == "split":
                    conditions_clause.append(cond.field.in_(args.get(cond.field.name)))
                else:
                    if cond.type is str:
                        conditions_clause.append(cond.field.ilike(f"%{args.get(cond.field.name)}%"))
                    elif cond.type is int:
                        conditions_clause.append(cond.field == args.get(cond.field.name))

    if code_label_clause is not None and not conditions_clause:
        return code_label_clause

    if code_label_clause is None and conditions_clause:
        return and_(*conditions_clause)

    return and_(code_label_clause, *conditions_clause)
