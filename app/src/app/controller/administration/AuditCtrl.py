from app.servicesapp.authentication.connected_user import ConnectedUser
from models.schemas.audit import AuditUpdateDataSchema
import sqlalchemy
from flask import current_app

from flask_restx import Namespace, Resource, fields
from flask_restx._http import HTTPStatus
from marshmallow_jsonschema import JSONSchema
from sqlalchemy.exc import NoResultFound

from app import db
from app.controller import ErrorController
from app.controller.Decorators import check_permission
from app.controller.utils.ControllerUtils import get_pagination_parser
from models.entities.audit.AuditUpdateData import AuditUpdateData
from app.models.common.Pagination import Pagination
from models.value_objects.common import DataType
from app.models.enums.AccountRole import AccountRole

api = Namespace(name="audit", path="/audit", description="API de récupération des audits")

parser_get = get_pagination_parser(default_limit=5)

auth = current_app.extensions["auth"]

schema_many = AuditUpdateDataSchema(many=True)

model_json = JSONSchema().dump(schema_many)["definitions"]["AuditUpdateDataSchema"]  # type: ignore
model_single_api = api.schema_model("AuditUpdateDataSchema", model_json)
pagination_model = api.schema_model("Pagination", Pagination.definition_jsonschema)

pagination_with_model = api.model(
    "AuditUpdateDataSchemaPagination",
    {"items": fields.List(fields.Nested(model_single_api)), "pageInfo": fields.Nested(pagination_model)},
)


@api.errorhandler(KeyError)
def handle_type_not_exist(e):
    return ErrorController("Type inconnu").to_json(), HTTPStatus.BAD_REQUEST


@api.route("/<type>")
@api.doc(params={"type": str([e.value for e in DataType])})
@api.doc(model=pagination_with_model)
class Audit(Resource):
    @api.response(200, "List of update data")
    @api.doc(security="Bearer")
    @api.expect(parser_get)
    @auth.token_auth("default", scopes_required=["openid"])
    @api.response(204, "No Result")
    @check_permission([AccountRole.ADMIN, AccountRole.COMPTABLE])
    def get(self, type: DataType):

        user = ConnectedUser.from_current_token_identity()
        clientId = user.azp

        args = parser_get.parse_args()
        enum_type = DataType[type]

        stmt = (
            db.select(AuditUpdateData)
            .where((AuditUpdateData.data_type == enum_type.name) & (AuditUpdateData.application_clientid == clientId))
            .order_by(AuditUpdateData.date.desc())
        )
        page_result = db.paginate(stmt, per_page=args.limit, page=args.page_number, error_out=False)

        if page_result.items == []:
            return "", HTTPStatus.NO_CONTENT

        schema_many = AuditUpdateDataSchema(many=True)
        result = schema_many.dump(page_result.items)

        return {
            "items": result,
            "pageInfo": Pagination(page_result.total, page_result.page, page_result.per_page).to_json(),
        }, HTTPStatus.OK


@api.route("/<type>/last")
class AuditLastImport(Resource):
    @auth.token_auth("default", scopes_required=["openid"])
    @api.doc(security="Bearer")
    @api.marshal_with(api.model("date-last-import", {"date": fields.DateTime}), code=200)
    def get(self, type: DataType):
        enum_type = DataType[type]

        user = ConnectedUser.from_current_token_identity()
        clientId = user.azp

        stmt = db.select(sqlalchemy.sql.functions.max(AuditUpdateData.date)).where(
            (AuditUpdateData.data_type == enum_type.name) & (AuditUpdateData.application_clientid == clientId)
        )

        result = db.session.execute(stmt).scalar_one_or_none()

        if result is None:
            return {"date": None}, HTTPStatus.OK

        return {"date": result.isoformat()}, HTTPStatus.OK
