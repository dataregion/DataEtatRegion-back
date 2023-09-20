from flask import current_app
from flask_restx import Namespace, Resource, fields

from app.models.tags.Tags import Tags, TagsSchema

api = Namespace(name="API Tags", path="/tags", description="API des tags")

auth = current_app.extensions["auth"]

tags_model = api.model("tags", model={"type": fields.String(), "value": fields.String()})


@api.route("")
@api.doc(model=tags_model)
class RefTags(Resource):
    @auth.token_auth("default", scopes_required=["openid"])
    @api.doc(security="Bearer")
    @api.response(200, "Success", fields.List(fields.Nested(tags_model)))
    def get(self):
        tags = Tags.query.all()
        result = TagsSchema(many=True).dump(tags)
        return result
