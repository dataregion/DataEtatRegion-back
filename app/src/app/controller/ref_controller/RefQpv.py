from app.controller.utils.ControllerUtils import positive
from app.models.common.Pagination import Pagination
from flask import current_app
from flask_restx import Namespace, Resource, reqparse, fields
from flask_restx._http import HTTPStatus
from marshmallow_jsonschema import JSONSchema
from models.entities.refs import Commune
from models.entities.refs.Qpv import Qpv
from models.entities.refs.QpvCommune import QpvCommune
from models.schemas.refs import QpvEnrichedSchema, QpvSchema
from sqlalchemy import and_, or_, select
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
parser_qpv.add_argument(
    "label_commune", type=str, required=False, help="Recherche sur le label de la commune associée", action=None
)
parser_qpv.add_argument("annee_decoupage", type=int, required=False, help="Année de découpage des QPV", action=None)


schema_many = QpvSchema(many=True)
model_json = JSONSchema().dump(schema_many)["definitions"]["QpvSchema"]
model_single_api = api.schema_model("Qpv", model_json)
pagination_model = api.schema_model("Pagination", Pagination.definition_jsonschema)


schema_many_qpv_with_commune = QpvEnrichedSchema(many=True)
model_json_qpv = JSONSchema().dump(schema_many_qpv_with_commune)["definitions"]["QpvEnrichedSchema"]
model_qpv_with_commune = api.schema_model("QpvWithCommune", model_json_qpv)

pagination_with_model = api.model(
    "QpvPagination",
    {"items": fields.List(fields.Nested(model_single_api)), "pageInfo": fields.Nested(pagination_model)},
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
                conditions.append(
                    or_(Qpv.code.ilike(f"%{args.get('query')}%"), Qpv.label.ilike(f"%{args.get('query')}%"))
                )
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

    @api.route("/region/<code_region>")
    class RefQpvRegion(Resource):
        @auth("openid")
        @api.doc(security="Bearer")
        @api.response(200, "Success", model_qpv_with_commune)
        def get(self, code_region):
            try:
                stmt = (
                    select(
                        Qpv.code,
                        Qpv.label,
                        Qpv.geom,
                        Qpv.centroid,
                        Commune.code.label("code_commune"),
                        Commune.label_commune.label("nom_commune"),
                        Commune.code_departement,
                        Commune.label_departement.label("nom_departement"),
                        Commune.code_epci,
                        Commune.label_epci.label("nom_epci"),
                    )
                    .join(QpvCommune, QpvCommune.qpv_id == Qpv.id)
                    .join(Commune, Commune.id == QpvCommune.commune_id)
                    .where(and_(Commune.code_region == code_region, Qpv.annee_decoupage == 2024))
                )
                result = db.session.execute(stmt).fetchall()
                qpvs = [dict(row._mapping) for row in result]
                schema_many = QpvEnrichedSchema(many=True)

                result = schema_many.dump(qpvs)
                return result, HTTPStatus.OK
            except NoResultFound:
                return "", HTTPStatus.NOT_FOUND
