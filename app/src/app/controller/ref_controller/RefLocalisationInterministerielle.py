from flask import current_app
from flask_restx import Namespace, Resource
from flask_restx._http import HTTPStatus

from app import db
from app.controller.ref_controller import build_ref_controller
from app.controller.utils.ControllerUtils import ParserArgument, get_pagination_parser
from app.models.common.Pagination import Pagination
from models.schemas.refs import (
    LocalisationInterministerielleSchema,
)
from models.entities.refs.LocalisationInterministerielle import LocalisationInterministerielle

auth = current_app.extensions["auth"]

api = build_ref_controller(
    LocalisationInterministerielle,
    LocalisationInterministerielleSchema,
    Namespace(
        name="Localisation interministerielle Controller",
        path="/loc-interministerielle",
        description="API referentiels des localisations interministerielles",
    ),
    cond_opt=(
        ParserArgument(
            LocalisationInterministerielle.site, str, "Recherche sur le site de la localisation interministérielle"
        ),
    ),
)

parser_get_loc_child = get_pagination_parser()


@api.route("/<code>/loc-interministerielle")
@api.doc(model=api.models["LocalisationInterministerielle"])
class RefLocalisationByCodeParent(Resource):
    @auth("openid")
    @api.doc(security="Bearer", description="Remonte les localisations ministerielle associées au code parent")
    @api.expect(parser_get_loc_child)
    @api.response(200, "Success", api.models["LocalisationInterministeriellePagination"])
    def get(self, code):
        args = parser_get_loc_child.parse_args()
        stmt = (
            db.select(LocalisationInterministerielle)
            .where(LocalisationInterministerielle.code_parent == code)
            .order_by(LocalisationInterministerielle.code)
        )

        page_result = db.paginate(stmt, per_page=args.limit, page=args.page_number, error_out=False)
        if page_result.items == []:
            return "", HTTPStatus.NO_CONTENT

        result = LocalisationInterministerielleSchema(many=True).dump(page_result.items)

        return {
            "items": result,
            "pageInfo": Pagination(page_result.total, page_result.page, page_result.per_page).to_json(),
        }, HTTPStatus.OK
