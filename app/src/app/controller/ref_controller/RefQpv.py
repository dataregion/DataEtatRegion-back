from app.controller.utils.ControllerUtils import positive
from app.models.common.Pagination import Pagination
from flask import current_app
from flask_restx import Namespace, Resource, reqparse, fields
from flask_restx._http import HTTPStatus
from marshmallow_jsonschema import JSONSchema
from models.entities.refs.Qpv import Qpv
from models.schemas.refs import QpvSchema
from sqlalchemy import and_, or_, text, bindparam
from sqlalchemy.exc import NoResultFound

from app import db

api = Namespace(name="Quartiers Prioritaire de la ville", path="/qpv", description="API referentiels des QPV")
parser_qpv = reqparse.RequestParser()
parser_qpv.add_argument("nom", type=str, required=False, help="Recherche sur le nom du CRTE")
parser_qpv.add_argument("departement", type=str, required=False, help="Recherche sur le numéro du département")
parser_qpv.add_argument("limit", type=int, required=False, default=500, help="Nombre de résultat")

auth = current_app.extensions["auth"]

qpv_model = api.model("qpv", model={"code": fields.String(), "nom": fields.String()})


parser_qpv = reqparse.RequestParser()
parser_qpv.add_argument("page_number", type=positive(), required=False, default=0, help="Numéro de la page de resultat")
parser_qpv.add_argument("limit", type=positive(), required=False, default=100, help="Nombre de résultat par page")
parser_qpv.add_argument("query", type=str, required=False, help="Recherche sur le code ou le label")
parser_qpv.add_argument("code_region", type=str, required=False, help="Code région du QPV", action=None)
parser_qpv.add_argument("code_commune", type=str, required=False, help="Code commune du QPV", action=None)
parser_qpv.add_argument("label_commune", type=str, required=False, help="Recherche sur le label de la commune associée", action=None)
parser_qpv.add_argument("annee_decoupage", type=int, required=False, help="Année de découpage des QPV", action=None)


schema_many = QpvSchema(many=True)
model_json = JSONSchema().dump(schema_many)["definitions"]["QpvSchema"]
model_single_api = api.schema_model("Qpv", model_json)
pagination_model = api.schema_model("Pagination", Pagination.definition_jsonschema)

pagination_with_model = api.model(
    "QpvPagination",
    {
        "items": fields.List(fields.Nested(model_single_api)),
        "pageInfo": fields.Nested(pagination_model)
    },
)


@api.route("/")
@api.doc(model=pagination_with_model)
class RefQpv(Resource):
    
    @api.route("")
    @api.doc(model=pagination_with_model)
    class RefQpvList(Resource):
        @auth("openid")
        @api.doc(security="Bearer")
        @api.expect(parser_qpv)
        @api.response(200, "Success", pagination_with_model)
        @api.response(204, "No Result")
        def get(self):
            args = parser_qpv.parse_args()

            # Condition sur code OR label
            conditions = []
            if args.get("query"):
                conditions.append(or_(
                    Qpv.code.ilike(f"%{args.get('query')}%"),
                    Qpv.label.ilike(f"%{args.get('query')}%")
                ))
            if args.get("code_region"):
                conditions.append(Qpv.communes.any(code_region=args.get("code_region")))
            if args.get("code_commune"):
                conditions.append(Qpv.communes.any(code_commune=args.get("code_commune")))
            if args.get("label_commune"):
                conditions.append(Qpv.label_commune.ilike(f"%{args.get("label_commune")}%"))
            if args.get("annee_decoupage"):
                conditions.append(Qpv.annee_decoupage == args.get("annee_decoupage"))

            
            if conditions:
                stmt = db.select(Qpv).where(and_(*conditions)).order_by(Qpv.code)
            else:
                stmt = db.select(Qpv).order_by(Qpv.code)

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
    class RefQpvCode(Resource):
        @auth("openid")
        @api.doc(security="Bearer")
        @api.response(200, "Success", model_single_api)
        def get(self, code):
            try:
                result = db.session.execute(db.select(Qpv).filter_by(code=code)).scalar_one()
                schema_m = QpvSchema()
                result = schema_m.dump(result)
                return result, HTTPStatus.OK
            except NoResultFound:
                return "", HTTPStatus.NOT_FOUND